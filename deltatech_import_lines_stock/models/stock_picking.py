# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "import.lines.mixin"]

    def _import_lines_check(self):
        self.ensure_one()
        if self.state in ("done", "cancel"):
            raise UserError(self.env._("Lines cannot be imported in a done or cancelled transfer."))
        return True

    @api.model
    def _import_lines_targets(self):
        return super()._import_lines_targets() + ["lot"]

    def _import_lines_partner(self):
        return self.partner_id

    def _import_lines_company(self):
        return self.company_id

    def _import_lines_product_domain(self):
        return super()._import_lines_product_domain() + [("type", "=", "consu")]

    def _import_lines_find_lot(self, product, lot_name):
        company = self._import_lines_company()
        return self.env["stock.lot"].search(
            [("name", "=", lot_name), ("product_id", "=", product.id), ("company_id", "in", [company.id, False])],
            limit=1,
        )

    def _import_lines_can_create_lots(self):
        return self.picking_type_code == "incoming" and self.picking_type_id.use_create_lots

    def _import_lines_check_row(self, row):
        error = super()._import_lines_check_row(row)
        lot_name = row.get("lot_name")
        if error or not lot_name:
            return error
        product = row["product"]
        if product.tracking == "none":
            return "lot_error", self.env._("%s is not tracked by lot or serial number.", product.display_name)
        if product.tracking == "serial" and row["quantity"] != 1:
            return "lot_error", self.env._("The quantity of serial number %s must be 1.", lot_name)
        if not self._import_lines_find_lot(product, lot_name) and not self._import_lines_can_create_lots():
            return "lot_error", self.env._("Lot %s does not exist and this operation cannot create lots.", lot_name)
        return False

    def _import_lines_prepare_move(self, row):
        product = row["product"]
        vals = {
            "product_id": product.id,
            "product_uom_qty": row["quantity"],
            "product_uom": (row["uom"] or product.uom_id).id,
            "location_id": self.location_id.id,
            "location_dest_id": self.location_dest_id.id,
        }
        if row.get("description"):
            vals["description_picking"] = row["description"]
        return vals

    def _import_lines_create(self, rows, wizard):
        self.ensure_one()
        # default_picking_id marks the moves added to a confirmed transfer as additional
        moves = (
            self.env["stock.move"]
            .with_context(default_picking_id=self.id)
            .create([dict(self._import_lines_prepare_move(row), picking_id=self.id) for row in rows])
        )
        # the lots are set before the confirmation, which can merge the new moves into the existing ones
        for row, move in zip(rows, moves, strict=True):
            if row.get("lot_name"):
                self._import_lines_set_lot(move, row)
        self._autoconfirm_picking()

    def _import_lines_set_lot(self, move, row):
        lot = self._import_lines_find_lot(move.product_id, row["lot_name"])
        move.move_line_ids.unlink()
        vals = move._prepare_move_line_vals(quantity=row["quantity"])
        if lot:
            vals["lot_id"] = lot.id
        else:
            vals["lot_name"] = row["lot_name"]
        self.env["stock.move.line"].create(vals)
