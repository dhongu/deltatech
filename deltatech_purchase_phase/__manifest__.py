# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Purchase Order Stage",
    "version": "19.0.1.2.6",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "summary": "Purchase Order Stage",
    "category": "Purchase",
    "depends": ["purchase_stock", "deltatech_widget_many2one_badge"],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_order_phase_view.xml",
        "views/purchase_order_view.xml",
        "data/purchase_order_phase_data.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
