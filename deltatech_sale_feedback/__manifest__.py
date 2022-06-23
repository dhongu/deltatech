# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Feedback",
    "summary": "Sale Feedback",
    "version": "14.0.1.0.2",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["sale", "account", "portal_rating"],
    "license": "LGPL-3",
    "data": [
        "data/mail_data.xml",
        "views/account_move_view.xml",
        "data/ir_cron_data.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
