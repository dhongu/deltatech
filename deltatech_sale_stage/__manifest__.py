# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Sale Order Stage",
    "version": "18.0.1.1.3",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "summary": "Sale Order Stage",
    "category": "Sales",
    "depends": ["sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_view.xml",
        "views/stock_picking_type_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
