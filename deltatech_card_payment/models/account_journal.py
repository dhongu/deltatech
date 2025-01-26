# ©  2024 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _default_inbound_payment_methods(self):
        res = super()._default_inbound_payment_methods()
        res |= self.env.ref("deltatech_card_payment.account_payment_method_card_in")
        return res
