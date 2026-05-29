# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Purchase UBL",
    "summary": "Import UBL XML vendor invoices to update prices, validate receipts, and create vendor bills",
    "version": "19.0.0.0.7",
    "category": "Purchases",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "depends": ["purchase", "stock", "account"],
    "data": [
        "views/ubl_import_wizard_views.xml",
        "security/ir.model.access.csv",
    ],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
    "images": ["static/description/main_screenshot.png"],
}
