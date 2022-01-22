# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ManualBackOrder(models.TransientModel):
    _name = "stock.picking.manual.backorder"
    _description = "ManualBackOrder"

    line_ids = fields.One2many("stock.picking.manual.backorder.line", "manual_backorder_id")

    def default_get(self, fields_list):
        defaults = super(ManualBackOrder, self).default_get(fields_list)
        active_id = self.env.context.get("active_id")
        picking = self.env["stock.picking"].browse(active_id)
        if picking.state in ["done", "cancel"]:
            raise UserError(_("The transfer status does not allow the change"))

        line_ids = []
        for move in picking.move_lines:
            values = {
                "product_id": move.product_id,
                "move_id": move.id,
                "product_uom_qty": move.product_uom_qty,
                "kept_qty": move.forecast_availability,
            }
            line_ids += [(0, 0, values)]
        defaults["line_ids"] = line_ids
        return defaults

    def do_create_backorder(self):
        quality = 0
        for line in self.line_ids:
            quality += line.kept_qty
        if quality:
            active_id = self.env.context.get("active_id")
            picking = self.env["stock.picking"].browse(active_id)

            backorder_picking = picking.copy(
                {"name": "/", "state": "draft", "move_lines": [], "move_line_ids": [], "backorder_id": picking.id}
            )
            picking.message_post(
                body=_("The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.")
                % (backorder_picking.id, backorder_picking.name)
            )

            for line in self.line_ids:
                if line.kept_qty == 0:
                    line.move_id.write({"picking_id": backorder_picking.id})
                    line.move_id.move_line_ids.package_level_id.write({"picking_id": backorder_picking.id})
                    line.move_id.mapped("move_line_ids").write({"picking_id": backorder_picking.id})
                else:
                    diff = line.product_uom_qty - line.kept_qty
                    if diff:
                        line.move_id.write({"product_uom_qty": line.kept_qty})
                        line.move_id.copy(
                            {"picking_id": backorder_picking.id, "product_uom_qty": diff, "move_line_ids": []}
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
