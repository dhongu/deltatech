# ©  2008-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import SUPERUSER_ID, api
from odoo.tools.sql import SQL, column_exists


def migrate(cr, version):
    if not version:
        return

    # Mutăm datele de pe product_template pe product_product (variante)
    # În Odoo 18, last_purchase_price a fost mutat pe product.product
    # Folosim ORM deoarece câmpul este company_dependent=True (stocat ca jsonb în Odoo 18)

    env = api.Environment(cr, SUPERUSER_ID, {})

    # Identificăm coloana sursă pe product_template.
    # Poate fi deja redenumită de o altă migrare (ex: 18.0.1.2.10 pre-migration)
    tmpl_col = None
    if column_exists(cr, "product_template", "last_purchase_price_tmpl_old_tmp"):
        tmpl_col = "last_purchase_price_tmpl_old_tmp"
    elif column_exists(cr, "product_template", "last_purchase_price"):
        tmpl_col = "last_purchase_price"

    if not tmpl_col:
        return

    # Preluăm toate prețurile din template-uri pentru a evita multiple interogări SQL în loop
    query = SQL(
        "SELECT id, %s FROM product_template WHERE %s IS NOT NULL AND %s > 0",
        SQL.identifier(tmpl_col),
        SQL.identifier(tmpl_col),
        SQL.identifier(tmpl_col),
    )
    cr.execute(query)
    tmpl_prices = {row[0]: row[1] for row in cr.fetchall()}

    if not tmpl_prices:
        return

    # Identificăm companiile
    company_ids = env["res.company"].search([]).ids
    for company_id in company_ids:
        # Căutăm produsele care aparțin acestor template-uri și nu au preț
        # Folosim ORM cu with_company pentru a gestiona corect câmpurile company_dependent
        products = (
            env["product.product"]
            .with_company(company_id)
            .search([("product_tmpl_id", "in", list(tmpl_prices.keys())), ("last_purchase_price", "=", 0)])
        )
        for product in products:
            price = tmpl_prices.get(product.product_tmpl_id.id)
            if price:
                product.last_purchase_price = price
