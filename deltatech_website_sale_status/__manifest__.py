# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Sale Order status",
    "category": "Website",
    "summary": "Order stage from stock and courier status, in the back office and the customer portal",
    "version": "20.0.2.0.13",
    "license": "OPL-1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["portal", "website_sale_stock", "deltatech_delivery_status", "sale_stock"],
    "data": [
        "views/sale_view.xml",
        "views/res_config_settings_views.xml",
        "views/templates.xml",
    ],
    "qweb": ["static/src/xml/*.xml"],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
