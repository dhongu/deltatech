# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _should_create_payment(self):
        # A provider without payment method line on its journal ("none", or a wire transfer without
        # account_payment_custom) cannot have an account.payment: _create_payment raised on every
        # cron run and the order was never confirmed nor invoiced. The accountant records the
        # payment of such a transaction from the bank statement.
        if not super()._should_create_payment():
            return False
        payment_method_line = self.provider_id.journal_id.inbound_payment_method_line_ids.filtered(
            lambda line: line.payment_provider_id == self.provider_id
        )
        if not payment_method_line:
            _logger.info(
                "No payment created for transaction %s: provider %s has no payment method line.",
                self.reference,
                self.provider_id.name,
            )
            return False
        return True

    def _create_payment(self, **extra_create_values):
        if self.env.context.get("payment_date") and "date" not in extra_create_values:
            extra_create_values["date"] = self.env.context["payment_date"]
        return super()._create_payment(**extra_create_values)
