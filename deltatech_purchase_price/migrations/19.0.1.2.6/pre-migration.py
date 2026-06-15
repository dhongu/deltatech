import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Copy last_purchase_price from product_template to product_product (company_dependent jsonb).

    Previously the field lived on product_template as a plain float.
    Now it lives on product_product as company_dependent (jsonb column).
    Copy data for templates with a single variant so no price is lost.
    """
    # Drop stale column on product_template — Odoo will recreate it as computed (no store)
    cr.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'product_template'
          AND column_name = 'last_purchase_price'
        """
    )
    if cr.fetchone():
        # Copy value to single-variant products before dropping
        cr.execute(
            """
            UPDATE product_product pp
               SET last_purchase_price = pt.last_purchase_price
              FROM product_template pt
             WHERE pp.product_tmpl_id = pt.id
               AND pt.last_purchase_price IS NOT NULL
               AND pt.last_purchase_price != 0
               AND (
                   SELECT COUNT(*) FROM product_product pp2
                    WHERE pp2.product_tmpl_id = pt.id
                      AND pp2.active = TRUE
               ) = 1
            """
        )
        rows = cr.rowcount
        _logger.info("deltatech_purchase_price migration: copied last_purchase_price to %d product_product rows", rows)
        cr.execute("ALTER TABLE product_template DROP COLUMN IF EXISTS last_purchase_price")
        _logger.info("deltatech_purchase_price migration: dropped last_purchase_price from product_template")
