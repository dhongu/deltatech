# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _create_payment(self, **extra_create_values):
        # Odoo has no account.payment.method for the providers without online payment (wire transfer,
        # "none"), so their journal has no payment method line and the payment cannot be created:
        # the cron raised on every run for 4 days and the order was never confirmed nor invoiced.
        # The payment of such a transaction is recorded by the accountant, from the bank statement.
        payment_method_line = self.provider_id.journal_id.inbound_payment_method_line_ids.filtered(
            lambda line: line.payment_provider_id == self.provider_id
        )
        if not payment_method_line:
            _logger.info(
                "No payment created for transaction %s: provider %s has no payment method line.",
                self.reference,
                self.provider_id.name,
            )
            return self.env["account.payment"]
        if self.env.context.get("payment_date") and "date" not in extra_create_values:
            extra_create_values["date"] = self.env.context["payment_date"]
        return super()._create_payment(**extra_create_values)
