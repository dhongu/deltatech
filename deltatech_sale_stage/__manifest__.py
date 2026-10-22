# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Sale Order Phases",
    "version": "20.0.1.2.9",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "summary": "Custom fulfilment stages on sale orders: prepared, shipped, delivered",
    "category": "Sales",
    "depends": ["sale_stock", "deltatech_widget_many2one_badge"],
    "data": [
        "security/ir.access.csv",
        "views/sale_view.xml",
        "views/stock_picking_type_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
