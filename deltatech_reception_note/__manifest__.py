# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Batch Reception Note",
    "summary": "Receive vendor deliveries on reception notes drawn from open purchase quantities",
    "version": "19.0.0.1.8",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",
    "category": "Stock",
    "external_dependencies": {"python": []},
    "depends": ["purchase_stock"],
    "data": [
        "views/purchase_view.xml",
        "wizard/reception_note.xml",
        "security/ir.model.access.csv",
    ],
    "license": "LGPL-3",
    "development_status": "Production/Stable",
    "images": ["static/description/main_screenshot.png"],
    "maintainers": ["dhongu", "danila12", "VoicuStefan2001"],
}
