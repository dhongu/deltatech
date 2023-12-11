# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Product Valuation",
    "summary": "Product Valuation",
    "version": "15.0.0.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": [
        "product",
        "stock",
        "stock_account",
    ],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/valuation_area_view.xml",
        "views/product_valuation_view.xml",
        "views/account_account_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Alpha",
    "maintainers": ["dhongu"],
}
