# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Sale → Purchase RFQ (Alternative Purchase Orders)",
    "summary": "Create Purchase RFQ(s) from Sales Quotations and link them back to the quote.",
    "version": "19.0.1.1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Stock",
    "depends": ["purchase", "sale"],
    "license": "OPL-1",
    "data": [
        "views/sale_order_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
