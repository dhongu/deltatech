# ©  2008-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    if not version:
        return

    # Mutăm datele de pe product_template pe product_product (variante)
    # În Odoo 18, last_purchase_price a fost mutat pe product.product

    cr.execute("""
        UPDATE product_product p
        SET last_purchase_price = t.last_purchase_price
        FROM product_template t
        WHERE p.product_tmpl_id = t.id
          AND (p.last_purchase_price IS NULL OR p.last_purchase_price = 0)
          AND t.last_purchase_price > 0
    """)
