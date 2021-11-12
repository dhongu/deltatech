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
        states={"draft": [("readonly", False)], "in_progress": [("readonly", False)]},
    )

    direction = fields.Selection([("incoming", "Incoming"), ("outgoing", "Outgoing")])

    reference = fields.Char("Reference")

    note = fields.Text("Note")

    def _compute_move_ids(self):
        super(StockPickingBatch, self)._compute_move_ids()
        for batch in self:
            batch.received_move_line_ids = False
            if batch.move_line_ids:
                for move_line in batch.move_line_ids:
                    if move_line.qty_done > 0:
                        batch.received_move_line_ids |= move_line

    def action_done(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        batch_keep_pickings = safe_eval(get_param("deltatech_batch_keep_pickings", "False"))
        if batch_keep_pickings:
            return super(StockPickingBatch, self.with_context(from_batch=True)).action_done()
        else:
            pickings = self.mapped("picking_ids").filtered(lambda p: p.state not in ("cancel", "done"))
            for picking in pickings:
                move_lines = picking.move_line_ids.filtered(lambda r: r.qty_done)
                if not move_lines:  # picking has no qty done lines
                    self.write({"picking_ids": [(3, picking.id)]})  # remove picking from batch
            return super(StockPickingBatch, self).action_done()

    def action_cancel(self):
        res = super(StockPickingBatch, self).action_cancel()
        if res:
            batch_pickings = self.env["stock.picking"].search([("batch_id", "=", self.id)])
            batch_pickings.write({"batch_id": False})
        return res
