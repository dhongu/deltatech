# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "MRP Warehouse",
    "summary": "MRP Warehouse",
    "version": "15.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": ["stock", "product"],
    "license": "LGPL-3",
    "data": [
        "views/company_view.xml",
        "views/stock_warehouse_view.xml",
        "views/template_product_view.xml",
        # 'data/data.xml'
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
