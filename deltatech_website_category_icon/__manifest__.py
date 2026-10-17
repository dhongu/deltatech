# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "eCommerce Category Icons",
    "category": "Website",
    "summary": "SVG icons for eCommerce categories, shown in the shop",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale"],
    "data": [
        "views/product_public_category_views.xml",
        "views/shop_template.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_category_icon/static/src/scss/category_icon.scss",
        ],
    },
    "development_status": "Alpha",
    "maintainers": ["dhongu"],
}
