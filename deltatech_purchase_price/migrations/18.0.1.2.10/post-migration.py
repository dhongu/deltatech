# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tools.sql import column_exists


def migrate(cr, version):
    if column_exists(cr, "product_product", "last_purchase_price_old_tmp"):
        # In Odoo 18, company_dependent fields are stored as jsonb columns in the model's table.
        # The format is {"company_id": value}.
        # We migrate data from the temporary column to the new jsonb column.

        # Get all companies
        cr.execute("SELECT id FROM res_company")
        company_ids = [row[0] for row in cr.fetchall()]

        if company_ids:
            # We migrate the old value to all existing companies to maintain previous shared behavior.
            # Using SQL to build the jsonb object: jsonb_object_agg(company_id, price)
            # But since we have many companies for one product, we can use a more direct approach.

            # For each product, create a jsonb object with all company IDs mapping to the old price.
            # We can use jsonb_build_object in a loop or a complex SQL.

            # Simpler approach: update the last_purchase_price column with a jsonb object
            # that contains all company IDs.

            for company_id in company_ids:
                cr.execute(
                    """
                    UPDATE product_product
                    SET last_purchase_price = COALESCE(last_purchase_price, '{}'::jsonb) || jsonb_build_object(%s, last_purchase_price_old_tmp)
                    WHERE last_purchase_price_old_tmp IS NOT NULL AND last_purchase_price_old_tmp != 0
                """,
                    (str(company_id),),
                )

        # drop the column after migration
        cr.execute("ALTER TABLE product_product DROP COLUMN last_purchase_price_old_tmp")

    if column_exists(cr, "product_template", "last_purchase_price_tmpl_old_tmp"):
        cr.execute("ALTER TABLE product_template DROP COLUMN last_purchase_price_tmpl_old_tmp")
