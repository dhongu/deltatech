# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Purchase UBL",
    "summary": "Import UBL XML vendor invoices to update prices, validate receipts, and create vendor bills",
    "version": "17.0.1.2.0",
    "category": "Purchases",
    "author": "Deltatech",
    "license": "OPL-1",
    "website": "https://www.deltatech.ro",
    "depends": ["purchase", "stock", "account"],
    "data": [
        "views/ubl_import_wizard_views.xml"
    ],
    "assets": {},
    "installable": True,
    "application": False,
}
