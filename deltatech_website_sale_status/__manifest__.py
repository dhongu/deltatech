# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Sale Order status",
    "category": "Website",
    "summary": "Additional filters sales orders by status ",
    "version": "18.0.2.0.3",
    "license": "OPL-1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale_stock", "deltatech_delivery_status", "sale_stock"],
    "data": [
        "views/sale_view.xml",
        "views/templates.xml",
    ],
    "qweb": ["static/src/xml/*.xml"],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
    "assets": {
        "web.assets_backend": [
            # "/eltatech_website_sale_status/static/src/js/website_sale_backend.js"
        ],
    },
}
