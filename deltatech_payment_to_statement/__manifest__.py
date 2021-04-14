# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Payment to Statement",
    "version": "12.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "And payment to statement",
    "category": "Accounting",
    "depends": ["account", "payment", "deltatech_merge"],
    "license": "LGPL-3",
    "data": [
        "views/account_payment_view.xml",
        "views/account_view.xml",
        "views/account_journal_dashboard_view.xml",
        "wizard/merge_statement_view.xml",
        "data/data.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "post_init_hook": "_set_auto_auto_statement",
    "development_status": "stable",
    "maintainers": ["dhongu"],
}
