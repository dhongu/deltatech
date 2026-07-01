from odoo.tools import SQL


def migrate(cr, version):
    # arch_db al view-ului 'product_item_code' a fost suprascris în trecut prin
    # editorul website (customize_show="True"), cu un xpath pe //div[@itemprop='offers']
    # care nu mai există în website_sale.products_item pe 19.0. Il stergem impreuna cu
    # ir.model.data, ca la reincarcarea datelor modulului sa fie recreat curat din XML.
    cr.execute(
        SQL("""
        DELETE FROM ir_ui_view
        WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'deltatech_website_product_code'
              AND name = 'product_item_code'
              AND model = 'ir.ui.view'
        )
    """)
    )
    cr.execute(
        SQL("""
        DELETE FROM ir_model_data
        WHERE module = 'deltatech_website_product_code'
          AND name = 'product_item_code'
          AND model = 'ir.ui.view'
    """)
    )
