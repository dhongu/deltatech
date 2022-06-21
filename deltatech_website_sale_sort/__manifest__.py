# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Product sort",
    "category": "Website",
    "summary": "Additional sorting criteria ",
    "version": "14.0.1.0.2",
    "license": "LGPL-3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale"],
    "data": [
        "views/templates.xml",
        "data/ir_cron_data.xml",
        "views/res_config_settings_views.xml",
        "views/product.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
