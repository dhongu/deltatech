# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Payment to Statement",
    "summary": "Add payment to cash statement",
    "version": "13.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Accounting",
    "depends": ["account", "deltatech_merge"],
    "license": "LGPL-3",
    "data": [
        "views/account_payment_view.xml",
        "views/account_view.xml",
        "views/account_journal_dashboard_view.xml",
        "wizard/merge_statement_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "post_init_hook": "_set_auto_auto_statement",
    "development_status": "stable",
    "maintainers": ["dhongu"],
}
