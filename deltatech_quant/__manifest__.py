# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Pozitii Stoc",
    "version": "12.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Generic module",
    "category": "Administration",
    "depends": ["web", "base", "stock", "deltatech_product_extension"],
    "license": "LGPL-3",
    "images": ["static/description/main_screenshot.png"],
    "data": [
        "views/stock_view.xml",
        "wizard/stock_quant_report_view.xml",
        "views/stock_profit_view.xml",
        "wizard/stock_quant_change_lot_view.xml",
        "wizard/stock_quant_split_view.xml",
        "security/ir.model.access.csv",
    ],
    "development_status": "stable",
    "maintainers": ["dhongu"],
}
