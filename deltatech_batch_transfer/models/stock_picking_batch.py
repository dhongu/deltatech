# © Terrabit
# See LICENSE file for full copyright and licensing details.


from odoo import models

# from odoo.exceptions import UserError


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    def action_done(self):
        if self.env["ir.config_parameter"].get_param("deltatech_batch_keep_pickings", False):
            return super(StockPickingBatch, self.with_context(from_batch=True)).action_done()
        else:
            pickings = self.mapped("picking_ids").filtered(lambda p: p.state not in ("cancel", "done"))
            for picking in pickings:
                move_lines = picking.move_line_ids.filtered(lambda r: r.qty_done)
                if not move_lines:  # picking has no qty done lines
                    self.write({"picking_ids": [(3, picking.id)]})  # remove picking from batch
            return super(StockPickingBatch, self).action_done()
