# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Payment to Statement",
    "summary": "Add payment to cash statement",
    "version": "15.0.1.1.4",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Accounting",
    "depends": ["account"],
    "license": "OPL-1",
    "data": [
        "data/ir_config_param.xml",
        "views/account_payment_view.xml",
        "views/account_view.xml",
        "views/account_journal_dashboard_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "post_init_hook": "_set_auto_auto_statement",
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
