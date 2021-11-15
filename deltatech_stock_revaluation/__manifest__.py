# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Stock Revaluation",
    "version": "14.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Generic module",
    "category": "Administration",
    "depends": ["stock", "stock_account"],
    "license": "LGPL-3",
    "images": ["static/description/main_screenshot.png"],
    "data": [
        "security/stock_revaluation_security.xml",
        "views/stock_view.xml",
        "views/stock_revaluation_view.xml",
        "data/stock_revaluation_data.xml",
        "security/ir.model.access.csv",
        "views/deltatech_stock_revaluation.xml",
    ],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
