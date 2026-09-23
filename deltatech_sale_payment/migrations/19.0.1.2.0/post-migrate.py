# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
"""Recompute the stored payment fields of every sale order.

Values left by 18.0 were computed with the old logic (transactions without an
accounting payment were subtracted from the invoice amount, see 19.0.1.1.5), and
columns created by the pre-migration are empty: both are rebuilt with the ORM, in
batches so memory stays flat on large databases.
"""

import logging

from odoo import SUPERUSER_ID, api
from odoo.tools import split_every

_logger = logging.getLogger(__name__)

FIELDS = ("payment_amount", "payment_status", "provider_id")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    SaleOrder = env["sale.order"].with_context(active_test=False)
    fields_ = [SaleOrder._fields[name] for name in FIELDS]
    ids = SaleOrder.search([]).ids
    _logger.info("deltatech_sale_payment: recompute payment fields on %s sale orders", len(ids))
    for batch in split_every(1000, ids):
        orders = SaleOrder.browse(batch)
        for field in fields_:
            env.add_to_compute(field, orders)
        orders.flush_recordset(list(FIELDS))
        env.invalidate_all()
