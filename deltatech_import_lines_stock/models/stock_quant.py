# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.exceptions import UserError

from .lot_lookup import duplicate_serials, find_lots


class StockQuant(models.Model):
    _name = "stock.quant"
    _inherit = ["stock.quant", "import.lines.mixin"]

    def _import_lines_check(self):
        if not self.env.user.has_group("stock.group_stock_user"):
            raise UserError(self.env._("Only inventory users can import inventory counts."))
        return True

    @api.model
    def _import_lines_targets(self):
        return ["product", "quantity", "uom", "lot"]

    @api.model
    def _import_lines_allow_zero_quantity(self):
        return True

    def _import_lines_product_domain(self):
        return super()._import_lines_product_domain() + [("is_storable", "=", True)]

    def _import_lines_check_rows(self, rows):
        errors = super()._import_lines_check_rows(rows)
        lots = find_lots(self.env, self._import_lines_company(), rows)
        duplicates = duplicate_serials(rows)
        return [
            error or self._import_lines_check_lot(row, lots, duplicates)
            for row, error in zip(rows, errors, strict=True)
        ]

    def _import_lines_check_lot(self, row, lots, duplicates):
        lot_name = row.get("lot_name")
        if not lot_name:
            return False
        product = row["product"]
        if product.tracking == "none":
            return "lot_error", self.env._("%s is not tracked by lot or serial number.", product.display_name)
        if product.tracking == "serial" and row["quantity"] > 1:
            return "lot_error", self.env._("The quantity of serial number %s cannot be more than 1.", lot_name)
        if (product.id, lot_name) in duplicates:
            return "lot_error", self.env._("Serial number %s appears on several rows.", lot_name)
        if (product.id, lot_name) not in lots:
            return "lot_error", self.env._("Lot %s does not exist.", lot_name)
        return False

    def _import_lines_create(self, rows, wizard):
        location = wizard.location_id
        if not location:
            raise UserError(self.env._("Select the location of the inventory count."))
        # rows of the same product and lot are counted together
        lots = find_lots(self.env, self._import_lines_company(), rows)
        counted = {}
        for row in rows:
            product = row["product"]
            lot = lots.get((product.id, row.get("lot_name")), self.env["stock.lot"])
            quantity = row["uom"]._compute_quantity(row["quantity"], product.uom_id) if row["uom"] else row["quantity"]
            counted[product, lot] = counted.get((product, lot), 0.0) + quantity
        for (product, lot), quantity in counted.items():
            if lot and product.tracking == "serial" and quantity > 1:
                raise UserError(
                    self.env._(
                        "Serial number %(lot)s of %(product)s is counted more than once.",
                        lot=lot.name,
                        product=product.display_name,
                    )
                )
        Quant = self.with_context(inventory_mode=True)
        for (product, lot), quantity in counted.items():
            Quant.create(
                {
                    "product_id": product.id,
                    "location_id": location.id,
                    "lot_id": lot.id,
                    "inventory_quantity": quantity,
                }
            )
