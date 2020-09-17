# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Product Refurbish",
    "version": "14.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Purchase",
    "depends": ["stock", "stock_account", "purchase_stock", "website_sale_stock"],
    "license": "LGPL-3",
    "data": [
        # 'data/data.xml',
        # 'views/stock_move_view.xml',
        "views/stock_production_lot_view.xml",
        "views/sale_order_views.xml",
        "views/templates.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
}
