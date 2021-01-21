# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "MRP Cost",
    "version": "13.0.2.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Manufacturing",
    "depends": ["mrp", "stock", "sale", "product", "deltatech_warehouse", "deltatech_purchase_price"],
    "license": "LGPL-3",
    "data": [
        "views/mrp_view.xml",
        "data/mrp_data.xml",
        "views/mrp_production_templates.xml",
        "views/mrp_workcenter_view.xml",
        "views/product_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
