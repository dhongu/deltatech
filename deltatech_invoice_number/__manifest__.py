{
    "images": ["static/description/main_screenshot.png"],
    "name": "Invoice Number",
    "summary": "Renumbering invoice",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Accounting",
    "depends": ["account"],
    "license": "OPL-1",
    "data": [
        "security/sale_security.xml",
        "views/account_journal.xml",
        "wizard/account_invoice_change_number_view.xml",
        "security/ir.model.access.csv",
    ],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
