# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Product Valuation",
    "summary": "Product Stock Valuation",
    "version": "17.0.0.0.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Inventory/Inventory",
    "depends": ["stock_account", "deltatech_obyc"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/product_template_views.xml",
        "views/product_valuation_view.xml",
        "views/account_account_view.xml",
        "data/data.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Alpha",
    "maintainers": ["dhongu"],
}
