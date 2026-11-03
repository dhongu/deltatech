# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Batch Reception Note",
    "summary": "Receive vendor deliveries on reception notes drawn from open purchase quantities",
    "version": "20.0.0.1.7",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",
    "category": "Stock",
    "external_dependencies": {"python": []},
    "depends": ["purchase_stock"],
    "data": [
        "views/purchase_view.xml",
        "wizard/reception_note.xml",
        "security/ir.access.csv",
    ],
    "license": "LGPL-3",
    "development_status": "Production/Stable",
    "images": ["static/description/main_screenshot.png"],
    "maintainers": ["dhongu"],
}
