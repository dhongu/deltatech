# ©  2025 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _set_done(self, state_message=None, extra_allowed_states=()):
        txs_to_process = super()._set_done(state_message=state_message, extra_allowed_states=extra_allowed_states)
        for tx in txs_to_process:
            if tx.provider_id.postponed_delivery:
                sale_orders = tx.sale_order_ids.filtered("postponed_delivery")
                for sale_order in sale_orders:
                    # a failure to release the delivery must not block the payment processing
                    try:
                        sale_order.release_delivery()
                    except Exception:
                        _logger.exception("Failed to release postponed delivery for order %s", sale_order.name)

        return txs_to_process
