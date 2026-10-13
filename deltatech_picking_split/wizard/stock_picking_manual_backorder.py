# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import UserError


class ManualBackOrder(models.TransientModel):
    _name = "stock.picking.manual.backorder"
    _description = "ManualBackOrder"

    line_ids = fields.One2many("stock.picking.manual.backorder.line", "manual_backorder_id")

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        picking = self.env["stock.picking"].browse(active_id)
        if picking.state in ["done", "cancel"]:
            raise UserError(self.env._("The transfer status does not allow the change"))

        line_ids = []
        for move in picking.move_ids:
            values = {
                "product_id": move.product_id.id,
                "move_id": move.id,
                "product_uom_qty": move.product_uom_qty,
                "kept_qty": move.forecast_availability,
            }
            line_ids += [(0, 0, values)]
        defaults["line_ids"] = line_ids
        return defaults

    def _check_kept_quantities(self, picking):
        # the onchange only guards the form; RPC/imports reach this method directly and the
        # wizard may be stale, so the bounds are checked against the current move demand
        if picking.state in ["done", "cancel"]:
            raise UserError(self.env._("The transfer status does not allow the change"))
        for line in self.line_ids:
            move = line.move_id
            if move.picking_id != picking:
                raise UserError(
                    self.env._("The move of %s does not belong to this transfer.", line.product_id.display_name)
                )
            if move.product_uom.compare(line.kept_qty, 0.0) < 0 or (
                move.product_uom.compare(line.kept_qty, move.product_uom_qty) > 0
            ):
                raise UserError(
                    self.env._(
                        "The kept quantity of %(product)s must be between 0 and the demand %(demand)s.",
                        product=line.product_id.display_name,
                        demand=move.product_uom_qty,
                    )
                )

    def do_create_backorder(self):
        active_id = self.env.context.get("active_id")
        picking = self.env["stock.picking"].browse(active_id)
        self._check_kept_quantities(picking)
        quality = 0
        for line in self.line_ids:
            quality += line.kept_qty
        if quality:
            backorder_picking = picking.copy(
                {
                    "name": "/",
                    "state": "draft",
                    "move_ids": [],
                    "move_line_ids": [],
                    "backorder_id": picking.id,
                }
            )
            picking.message_post(
                body=self.env._(
                    "The backorder <a href=# data-oe-model=stock.picking "
                    "data-oe-id=%(backorder_id)d>%(backorder_name)s</a> has been created.",
                    backorder_id=backorder_picking.id,
                    backorder_name=backorder_picking.name,
                )
            )

            for line in self.line_ids:
                if line.kept_qty == 0:
                    line.move_id.write({"picking_id": backorder_picking.id})
                    line.move_id.mapped("move_line_ids").write({"picking_id": backorder_picking.id})
                else:
                    diff = line.move_id.product_uom_qty - line.kept_qty
                    if not line.move_id.product_uom.is_zero(diff):
                        line.move_id.write({"product_uom_qty": line.kept_qty})
                        line.move_id.copy(
                            {
                                "picking_id": backorder_picking.id,
                                "product_uom_qty": diff,
                                "move_line_ids": [],
                            }
                        )
            # backorder_picking.action_assign()


class ManualBackOrderLine(models.TransientModel):
    _name = "stock.picking.manual.backorder.line"
    _description = "ManualBackOrderLine"

    manual_backorder_id = fields.Many2one("stock.picking.manual.backorder")
    product_id = fields.Many2one("product.product", readonly=True)
    move_id = fields.Many2one("stock.move", readonly=True)
    product_uom_qty = fields.Float(string="Demand", readonly=True)
    kept_qty = fields.Float(string="Kept")

    @api.onchange("kept_qty")
    def onchange_kept_qty(self):
        if self.kept_qty > self.product_uom_qty or self.kept_qty < 0:
            self.kept_qty = self.product_uom_qty
