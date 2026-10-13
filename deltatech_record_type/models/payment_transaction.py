# ©  2026 Terrabit Solutions
# See README.rst file on addons root folder for license details

from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _check_amount_and_confirm_order(self):
        # the order is confirmed by the online payment, not by a user that has to choose the order type
        txs = self.with_context(record_type_payment_confirm=True)
        return super(PaymentTransaction, txs)._check_amount_and_confirm_order()
