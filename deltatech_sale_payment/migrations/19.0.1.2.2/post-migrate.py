# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
"""SALEPAY-001: the amount paid of the orders in a foreign currency was computed in the
company currency. Only those orders are recomputed, the others keep their values."""

import logging

from odoo import SUPERUSER_ID, api
from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        SQL(
            """
            SELECT so.id
              FROM sale_order so
              JOIN res_company rc ON rc.id = so.company_id
             WHERE so.currency_id != rc.currency_id
            """
        )
    )
    order_ids = [row[0] for row in cr.fetchall()]
    if not order_ids:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env["sale.order"].browse(order_ids)
    fnames = ["payment_amount", "payment_status", "provider_id"]
    for fname in fnames:
        env.add_to_compute(orders._fields[fname], orders)
    orders._recompute_recordset(fnames)
    _logger.info("deltatech_sale_payment: payment fields recomputed on %s foreign currency orders", len(orders))
