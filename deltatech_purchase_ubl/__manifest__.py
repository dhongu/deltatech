# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details
{
    "name": "Purchase UBL Import",
    "summary": "Import UBL XML vendor invoices to update prices, validate receipts, and create vendor bills",
    "version": "20.0.1.5.0",
    "category": "Purchases",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "consultant_sheet": "full",
    "website": "https://www.terrabit.ro",
    "depends": ["purchase_stock", "deltatech_account_ubl_import"],
    "data": [
        "views/ubl_import_wizard_views.xml",
        "security/ir.access.csv",
    ],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
    "images": ["static/description/main_screenshot.png"],
}
