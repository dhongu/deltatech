# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech SMS Delivery",
    "summary": "Send SMS la delivery events",
    "version": "13.0.1.0.0",
    "author": "Terrabit, Dorin Hongu, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Hidden",
    "depends": ["sale_stock", "stock", "sales_team", "sms"],
    "license": "LGPL-3",
    "data": [
        "data/sms_data.xml",
        "views/res_config_settings_views.xml",
        "security/ir.model.access.csv",
        "security/sms_security.xml",
        "views/stock_picking_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "stable",
    "maintainers": ["dhongu"],
}
