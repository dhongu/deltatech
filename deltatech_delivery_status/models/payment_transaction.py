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
                sale_order = tx.sale_order_id
                if sale_order and sale_order.postponed_delivery:
                    sale_order.release_delivery()

        return txs_to_process
