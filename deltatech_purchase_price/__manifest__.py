# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Purchase Price",
    "summary": "Update vendor price after reception",
    "version": "17.0.1.2.7",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Purchase",
    "depends": [
        "stock",
        "stock_account",
        "purchase_stock",
        "deltatech_product_trade_markup",
    ],
    "data": [
        "views/product_view.xml",
        "wizard/trade_markup_view.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
