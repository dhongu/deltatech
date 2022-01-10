# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech reception_note",
    "summary": "Batch reception note",
    "version": "14.0.0.0.3",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",
    "category": "Stock",
    "external_dependencies": {"python": []},
    "depends": ["purchase_stock"],
    "data": ["views/purchase_view.xml", "wizard/reception_note.xml", "security/ir.model.access.csv"],
    "license": "LGPL-3",
    "development_status": "Beta",
    "images": ["static/description/main_screenshot.png"],
    "maintainers": ["dhongu"],
}
