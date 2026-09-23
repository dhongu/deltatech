# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
"""Recompute the stored payment fields after the 18.0.1.2.1 fix.

Transactions confirmed on a provider without a journal have no accounting payment,
yet were subtracted from the amount paid on the invoice: the stored payment_amount
and payment_status of those orders are wrong and would stay so. Only the orders
with such a transaction on one of their invoices are recomputed.
"""

import logging

from odoo import SUPERUSER_ID, api
from odoo.tools import split_every

_logger = logging.getLogger(__name__)

FIELDS = ("payment_amount", "payment_status", "provider_id")


def migrate(cr, version):
    cr.execute(
        """
        SELECT DISTINCT sot.sale_order_id
          FROM sale_order_transaction_rel sot
          JOIN payment_transaction tx ON tx.id = sot.transaction_id
          JOIN account_invoice_transaction_rel ait ON ait.transaction_id = tx.id
         WHERE tx.state = 'done' AND tx.is_post_processed AND tx.payment_id IS NULL
        """
    )
    ids = [row[0] for row in cr.fetchall()]
    _logger.info("deltatech_sale_payment: recompute payment fields on %s sale orders", len(ids))
    env = api.Environment(cr, SUPERUSER_ID, {})
    SaleOrder = env["sale.order"].with_context(active_test=False)
    fields_ = [SaleOrder._fields[name] for name in FIELDS]
    for batch in split_every(1000, ids):
        orders = SaleOrder.browse(batch)
        for field in fields_:
            env.add_to_compute(field, orders)
        orders.flush_recordset(list(FIELDS))
        env.invalidate_all()
