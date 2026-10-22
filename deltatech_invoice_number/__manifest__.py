{
    "images": ["static/description/main_screenshot.png"],
    "name": "Invoice Numbering Control",
    "summary": "Enforce chronological invoice dates and let authorized users change invoice numbers",
    "version": "20.0.1.0.3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Accounting",
    "depends": ["account"],
    "license": "OPL-1",
    "data": [
        "security/sale_security.xml",
        "views/account_journal.xml",
        "wizard/account_invoice_change_number_view.xml",
        "security/ir.access.csv",
    ],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
