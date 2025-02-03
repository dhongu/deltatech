# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Products Alternative",
    "version": "17.0.2.0.9",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Alternative product codes",
    "category": "Sales",
    "depends": ["product", "stock", "sale", "purchase"],
    "license": "OPL-1",
    "data": [
        "views/product_template_view.xml",
        "views/product_product_view.xml",
        "views/product_alternative_view.xml",
        "views/sale_order_view.xml",
        "views/purchase_order_view.xml",
        "views/stock_move_view.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/stock_picking_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
