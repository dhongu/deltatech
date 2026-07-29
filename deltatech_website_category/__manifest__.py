# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Product Category",
    "category": "Website",
    "summary": "Public category",
    "version": "19.0.1.1.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale"],
    "data": ["views/shop_template.xml"],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_category/static/src/interactions/lazy_categories.js",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Alpha",
    "maintainers": ["dhongu"],
}
