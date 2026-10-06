# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_card_payment(self):
        self.ensure_one()
        return self.env["deltatech.card.payment"]._open_for(self)

    def action_view_card_receipts(self):
        self.ensure_one()
        return self.env["deltatech.expected.receipt"]._action_for_domain([("invoice_id", "=", self.id)])
