import logging

from odoo.tools import SQL

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


def copy_template_prices(cr, template_table="product_template", product_table="product_product"):
    """Copy the numeric template price into the company-dependent jsonb column of the variants.

    - the target column is created (jsonb) if missing, or converted if it is still numeric;
    - the value goes under the key of the template company, or of every company when the
      template is shared;
    - a value already present for a company on the variant is kept (data already migrated);
    - all active variants receive the value (a template with several variants had only
      this price, the vendor lines refine it afterwards).
    """
    pp_type = _col_type(cr, product_table, "last_purchase_price")
    if pp_type is None:
        cr.execute(SQL("ALTER TABLE %s ADD COLUMN last_purchase_price jsonb", SQL.identifier(product_table)))
    elif pp_type != "jsonb":
        table = SQL.identifier(product_table)
        cr.execute(SQL("ALTER TABLE %s RENAME COLUMN last_purchase_price TO last_purchase_price_old_tmp", table))
        cr.execute(SQL("ALTER TABLE %s ADD COLUMN last_purchase_price jsonb", table))
        cr.execute(
            SQL(
                "UPDATE %s SET last_purchase_price = (SELECT jsonb_object_agg(c.id::text, last_purchase_price_old_tmp) "
                "FROM res_company c) WHERE last_purchase_price_old_tmp IS NOT NULL AND last_purchase_price_old_tmp != 0",
                table,
            )
        )
        cr.execute(SQL("ALTER TABLE %s DROP COLUMN last_purchase_price_old_tmp", table))
    cr.execute(
        SQL(
            """
            UPDATE %(pp)s pp
               SET last_purchase_price = COALESCE(pp.last_purchase_price, '{}'::jsonb) || new_values.value
              FROM %(pt)s pt
              JOIN LATERAL (
                    SELECT pp3.id AS product_id, jsonb_object_agg(c.id::text, pt.last_purchase_price) AS value
                      FROM %(pp)s pp3, res_company c
                     WHERE pp3.product_tmpl_id = pt.id
                       AND (pt.company_id IS NULL OR c.id = pt.company_id)
                       AND NOT jsonb_exists(COALESCE(pp3.last_purchase_price, '{}'::jsonb), c.id::text)
                     GROUP BY pp3.id
                   ) new_values ON TRUE
             WHERE pp.product_tmpl_id = pt.id
               AND pp.id = new_values.product_id
               AND pp.active = TRUE
               AND pt.last_purchase_price IS NOT NULL
               AND pt.last_purchase_price != 0
            """,
            pp=SQL.identifier(product_table),
            pt=SQL.identifier(template_table),
        )
    )
    return cr.rowcount


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
        copy_template_prices(cr)
        cr.execute("ALTER TABLE product_template DROP COLUMN IF EXISTS last_purchase_price")
        _logger.info("deltatech_purchase_price: dropped last_purchase_price from product_template")
