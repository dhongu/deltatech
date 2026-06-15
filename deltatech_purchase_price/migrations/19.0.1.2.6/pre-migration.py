import logging

_logger = logging.getLogger(__name__)


def _col_type(cr, table, column):
    cr.execute(
        """
        SELECT data_type FROM information_schema.columns
         WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    row = cr.fetchone()
    return row[0] if row else None


def migrate(cr, version):
    """Migrate last_purchase_price: product_template (float) → product_product (company_dependent jsonb).

    Steps:
    1. If product_product.last_purchase_price already exists as plain float,
       convert it to company_dependent jsonb via util or SQL fallback.
    2. If product_template.last_purchase_price is a plain float,
       copy to product_product (for single-variant products), then drop from template.
    Odoo will create product_product.last_purchase_price as jsonb automatically
    if the column does not exist yet.
    """
    try:
        from odoo.upgrade import util
    except ImportError:
        util = None

    cr.execute("SELECT array_agg(id) FROM res_company")
    company_ids = cr.fetchone()[0] or []

    # --- Step 1: convert product_product.last_purchase_price float → jsonb if present ---
    pp_type = _col_type(cr, "product_product", "last_purchase_price")
    if pp_type and pp_type != "jsonb":
        _logger.info(
            "deltatech_purchase_price: converting product_product.last_purchase_price float → company_dependent jsonb"
        )
        if util is not None:
            util.make_field_company_dependent(cr, "product.product", "last_purchase_price", "float")
        else:
            _logger.info("odoo.upgrade.util not available, using SQL fallback")
            cr.execute(
                'ALTER TABLE product_product RENAME COLUMN "last_purchase_price" TO "last_purchase_price_old_tmp"'
            )
            cr.execute('ALTER TABLE product_product ADD COLUMN "last_purchase_price" jsonb')
            for company_id in company_ids:
                cr.execute(
                    """
                    UPDATE product_product
                       SET last_purchase_price = COALESCE(last_purchase_price, '{}'::jsonb)
                                                 || jsonb_build_object(%s, last_purchase_price_old_tmp)
                     WHERE last_purchase_price_old_tmp IS NOT NULL
                       AND last_purchase_price_old_tmp != 0
                    """,
                    (str(company_id),),
                )
            cr.execute('ALTER TABLE product_product DROP COLUMN "last_purchase_price_old_tmp"')

    # --- Step 2: copy template values to product_product, then drop template column ---
    pt_type = _col_type(cr, "product_template", "last_purchase_price")
    if pt_type and pt_type != "jsonb":
        _logger.info("deltatech_purchase_price: copying last_purchase_price from product_template to product_product")
        # Copy to single-variant products only; multi-variant products keep 0 (no safe default)
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
                    WHERE pp2.product_tmpl_id = pt.id AND pp2.active = TRUE
               ) = 1
            """
        )
        _logger.info("deltatech_purchase_price: copied %d rows", cr.rowcount)
        cr.execute("ALTER TABLE product_template DROP COLUMN IF EXISTS last_purchase_price")
        _logger.info("deltatech_purchase_price: dropped last_purchase_price from product_template")
