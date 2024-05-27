# © Terrabit
# See LICENSE file for full copyright and licensing details.


from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    received_move_line_ids = fields.One2many(
        "stock.move.line",
        compute="_compute_move_ids",
        string="Selected move lines",
        readonly=True,
    )

    direction = fields.Selection([("incoming", "Incoming"), ("outgoing", "Outgoing")])

    reference = fields.Char("Reference")

    note = fields.Text("Note")

    def _compute_move_ids(self):
        res = super()._compute_move_ids()
        for batch in self:
            batch.received_move_line_ids = False
            if batch.move_line_ids:
                for move_line in batch.move_line_ids:
                    if move_line.quantity > 0:
                        batch.received_move_line_ids |= move_line
        return res

    def action_done(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        batch_keep_pickings = safe_eval(get_param("deltatech_batch_keep_pickings", "False"))
        if batch_keep_pickings:
            return super(StockPickingBatch, self.with_context(from_batch=True)).action_done()
        else:
            pickings = self.mapped("picking_ids").filtered(lambda p: p.state not in ("cancel", "done"))
            for picking in pickings:
                move_lines = picking.move_ids.filtered(lambda r: r.quantity)
                if not move_lines:  # picking has no qty done lines
                    self.write({"picking_ids": [(3, picking.id)]})  # remove picking from batch
            return super().action_done()

    def action_cancel(self):
        res = super().action_cancel()
        if res:
            batch_pickings = self.env["stock.picking"].search([("batch_id", "=", self.id)])
            batch_pickings.write({"batch_id": False})
        return res
