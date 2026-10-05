from odoo import fields, models


class LedgerCancelWizard(models.TransientModel):
    _name = "ledger.cancel.wizard"
    _description = "Cancel Ledger Records"

    ledger_ids = fields.Many2many("ledger.ledger", string="Records")
    reason = fields.Text(string="Reason", required=True)

    def action_cancel(self):
        self.ensure_one()
        to_cancel = self.ledger_ids.filtered(lambda rec: rec.state in ("reserved", "active"))
        to_cancel.action_cancel(reason=self.reason)
        for rec in to_cancel:
            rec.message_post(body=self.env._("Canceled. Reason: %s", self.reason))
        return {"type": "ir.actions.act_window_close"}
