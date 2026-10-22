# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Stock Availability",
    "category": "Website",
    "summary": "eCommerce Stock Availability and lead time",
    "version": "19.0.1.0.13",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "live_test_url": "https://www.terrabit.ro/demo/deltatech_website_stock_availability?v=19.0",
    "depends": ["website", "website_sale_stock", "purchase", "deltatech_vendor_stock"],
    "data": [
        "views/product_view.xml",
        "views/website_sale_stock_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_stock_availability/static/src/js/**/*",
            "deltatech_website_stock_availability/static/src/xml/**/*",
            "deltatech_website_stock_availability/static/src/scss/**/*",
        ],
        "website.website_builder_assets": [
            "deltatech_website_stock_availability/static/src/website_builder/**/*",
        ],
        # "web.assets_tests": [
        #     "deltatech_website_stock_availability/static/tests/tours/stock_availability.tour.esm.js",
        # ],
    },
    "images": ["static/description/main_screenshot.png"],
    "price": 10.00,
    "currency": "EUR",
    "license": "OPL-1",
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
