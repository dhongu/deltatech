# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
"""payment_amount / payment_status / provider_id become stored again.

The values are computed here in SQL, set-based, before ``_auto_init``: the registry
finds the columns already filled and does not recompute every sale order through
the ORM, which on large databases would take hours. The SQL mirrors
``sale.order._compute_payment``; on a database coming from 18.0 the columns exist
and are rebuilt with the current rule.
"""

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        SQL(
            """
            ALTER TABLE sale_order
                ADD COLUMN IF NOT EXISTS payment_amount numeric,
                ADD COLUMN IF NOT EXISTS payment_status varchar,
                ADD COLUMN IF NOT EXISTS provider_id int4
            """
        )
    )
    compute_payment_fields(cr)


def compute_payment_fields(cr):
    """Fill the three stored fields of every sale order, like ``_compute_payment``."""
    cr.execute(
        SQL(
            """
            WITH tx AS (
                SELECT rel.sale_order_id AS order_id,
                       SUM(pt.amount) FILTER (WHERE pt.state = 'done') AS tx_paid,
                       BOOL_OR(pt.state = 'authorized') AS has_authorized,
                       BOOL_OR(pt.state = 'pending') AS has_pending,
                       BOOL_OR(pt.state = 'cancel') AS has_cancel
                  FROM sale_order_transaction_rel rel
                  JOIN payment_transaction pt ON pt.id = rel.transaction_id
                 GROUP BY rel.sale_order_id
            ),
            inv AS (
                SELECT sub.order_id, SUM(sub.paid) AS inv_paid
                  FROM (
                        SELECT DISTINCT sol.order_id, am.id,
                               am.amount_total_signed - am.amount_residual_signed AS paid
                          FROM sale_order_line sol
                          JOIN sale_order_line_invoice_rel rel ON rel.order_line_id = sol.id
                          JOIN account_move_line aml ON aml.id = rel.invoice_line_id
                          JOIN account_move am ON am.id = aml.move_id
                         WHERE am.state = 'posted'
                           AND am.move_type IN ('out_invoice', 'out_refund')
                       ) sub
                 GROUP BY sub.order_id
            ),
            provider AS (
                SELECT DISTINCT ON (rel.sale_order_id)
                       rel.sale_order_id AS order_id, pt.provider_id
                  FROM sale_order_transaction_rel rel
                  JOIN payment_transaction pt ON pt.id = rel.transaction_id
                 ORDER BY rel.sale_order_id,
                          CASE pt.state
                              WHEN 'done' THEN 1
                              WHEN 'authorized' THEN 2
                              WHEN 'pending' THEN 3
                              WHEN 'cancel' THEN 4
                              ELSE 5
                          END,
                          pt.id DESC
            ),
            computed AS (
                SELECT so.id,
                       GREATEST(0.0, COALESCE(inv.inv_paid, 0.0), COALESCE(tx.tx_paid, 0.0)) AS amount,
                       tx.order_id IS NOT NULL AS has_tx,
                       tx.has_authorized, tx.has_pending, tx.has_cancel,
                       provider.provider_id,
                       so.amount_total,
                       COALESCE(cur.rounding, 0.01) AS rounding
                  FROM sale_order so
                  LEFT JOIN tx ON tx.order_id = so.id
                  LEFT JOIN inv ON inv.order_id = so.id
                  LEFT JOIN provider ON provider.order_id = so.id
                  LEFT JOIN res_currency cur ON cur.id = so.currency_id
            )
            UPDATE sale_order so
               SET payment_amount = c.amount,
                   provider_id = c.provider_id,
                   payment_status = CASE
                       -- compare_amounts(amount, total) >= 0 within the currency rounding
                       WHEN c.amount > 0 AND c.amount - c.amount_total > -c.rounding / 2 THEN 'done'
                       WHEN c.amount > 0 THEN 'partial'
                       WHEN NOT c.has_tx THEN 'without'
                       WHEN c.has_authorized THEN 'authorized'
                       WHEN c.has_pending THEN 'pending'
                       WHEN c.has_cancel THEN 'cancelled'
                       ELSE 'initiated'
                   END
              FROM computed c
             WHERE c.id = so.id
            """
        )
    )
    _logger.info("deltatech_sale_payment: payment fields computed in SQL on %s sale orders", cr.rowcount)
