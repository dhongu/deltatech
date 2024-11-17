# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Stock Availability",
    "category": "Website",
    "summary": "eCommerce Stock Availability and lead time",
    "version": "18.0.1.0.3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["website", "website_sale_stock", "purchase", "deltatech_vendor_stock"],
    "data": [
        "views/product_view.xml",
        "views/website_sale_stock_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_stock_availability/static/src/js/variant_mixin.esm.js",
            "deltatech_website_stock_availability/static/src/xml/**/*",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "price": 10.00,
    "currency": "EUR",
    "license": "OPL-1",
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
