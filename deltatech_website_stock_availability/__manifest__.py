# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Stock Availability",
    "category": "Website",
    "summary": "eCommerce Stock Availability",
    "version": "15.0.1.0.2",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["website", "website_sale_stock", "purchase"],
    "data": [
        "views/product_view.xml",
        "views/website_sale_stock_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_stock_availability/static/src/js/**/*",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "price": 10.00,
    "currency": "EUR",
    "license": "LGPL-3",
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
