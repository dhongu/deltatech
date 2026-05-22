import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Backfilling sale.order.is_ready ...")

    # Orders in draft/sent: is_ready depends on qty_available vs qty_to_deliver.
    # Computing per-product stock in pure SQL is complex, so we mark them
    # as not-ready by default and let the ORM recompute via _recompute_all.
    # For confirmed orders (state='sale'): is_ready = all outgoing pickings done or
    # at least one move has reserved qty > 0 (direct policy) or all moves fully reserved.
    # The safest migration: mark cancelled/done orders definitively via SQL,
    # then trigger ORM recompute for the rest.

    # 1. Cancelled orders are never ready.
    cr.execute(
        SQL("""
        UPDATE sale_order
        SET is_ready = false
        WHERE state = 'cancel'
    """)
    )

    # 2. Invoiced orders are not ready (invoice_status = 'invoiced').
    cr.execute(
        SQL("""
        UPDATE sale_order
        SET is_ready = false
        WHERE invoice_status = 'invoiced'
    """)
    )

    # 3. Confirmed orders where all outgoing pickings are done or cancelled → ready.
    #    (picking_policy = 'one', all moves fully delivered)
    cr.execute(
        SQL("""
        UPDATE sale_order so
        SET is_ready = true
        WHERE so.state = 'sale'
          AND so.invoice_status != 'invoiced'
          AND NOT EXISTS (
              SELECT 1
              FROM stock_picking sp
              WHERE sp.sale_id = so.id
                AND sp.picking_type_code = 'outgoing'
                AND sp.state NOT IN ('done', 'cancel')
          )
          AND EXISTS (
              SELECT 1
              FROM stock_picking sp
              WHERE sp.sale_id = so.id
                AND sp.picking_type_code = 'outgoing'
          )
    """)
    )

    # 4. Confirmed orders with at least one pending outgoing picking that has
    #    all moves fully reserved (quantity = product_uom_qty) → ready (one policy).
    cr.execute(
        SQL("""
        UPDATE sale_order so
        SET is_ready = true
        WHERE so.state = 'sale'
          AND so.invoice_status != 'invoiced'
          AND so.picking_policy = 'one'
          AND is_ready = false
          AND EXISTS (
              SELECT 1
              FROM stock_picking sp
              JOIN stock_move sm ON sm.picking_id = sp.id
              WHERE sp.sale_id = so.id
                AND sp.picking_type_code = 'outgoing'
                AND sp.state NOT IN ('done', 'cancel')
              GROUP BY sp.id
              HAVING bool_and(sm.quantity >= sm.product_uom_qty)
          )
    """)
    )

    # 5. Confirmed orders with at least one move with reserved qty > 0 → ready (direct policy).
    cr.execute(
        SQL("""
        UPDATE sale_order so
        SET is_ready = true
        WHERE so.state = 'sale'
          AND so.invoice_status != 'invoiced'
          AND so.picking_policy = 'direct'
          AND is_ready = false
          AND EXISTS (
              SELECT 1
              FROM stock_picking sp
              JOIN stock_move sm ON sm.picking_id = sp.id
              WHERE sp.sale_id = so.id
                AND sp.picking_type_code = 'outgoing'
                AND sp.state NOT IN ('done', 'cancel')
                AND sm.quantity > 0
          )
    """)
    )

    cr.execute(SQL("SELECT COUNT(*) FROM sale_order WHERE is_ready = true"))
    count = cr.fetchone()[0]
    _logger.info("sale.order.is_ready backfill done: %d orders marked as ready.", count)
