# © Terrabit
# See LICENSE file for full copyright and licensing details.


from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        from_batch = self.env.context.get("from_batch")
        if not from_batch:
            return super(StockPicking, self).button_validate()
        else:
            all_pickings = self
            for picking in self:
                move_lines = picking.move_line_ids.filtered(lambda r: r.qty_done > 0)
                if not move_lines:
                    all_pickings -= picking
            if not all_pickings:
                raise UserError(_("No effective quantities set"))
            return super(StockPicking, all_pickings).button_validate()

    def add_to_batch(self):
        self.ensure_one()
        if not self.batch_id:
            xml_id = "stock_picking_batch.stock_picking_to_batch_action_stock_picking"
            action = self.env["ir.actions.actions"]._for_xml_id(xml_id)

            # batch = self.env["stock.picking.batch"].create(
            #     {
            #         "direction": self.picking_type_code,
            #         "reference": self.name,
            #         "partner_id": self.partner_id.id,
            #     }
            # )
            # self.write({"batch_id": batch.id})
            # lots = self.move_line_ids.mapped("lot_id")
            # if not lots:
            #     batch.action_confirm()
            # action = self.env["ir.actions.actions"]._for_xml_id("stock_picking_batch.stock_picking_batch_action")
            # action["context"] = {}
            # action["domain"] = [("id", "=", batch.id)]
            return action
        else:
            raise UserError(_("This picking is already in a batch"))
