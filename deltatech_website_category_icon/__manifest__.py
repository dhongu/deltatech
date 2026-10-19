# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "eCommerce Category Icons",
    "category": "Website",
    "summary": "SVG icons for eCommerce categories, shown in the shop",
    "version": "19.0.1.3.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale"],
    "data": [
        "views/product_public_category_views.xml",
        "views/shop_template.xml",
        "views/res_config_settings_views.xml",
        "views/snippets/s_category_icon_grid.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_category_icon/static/src/scss/category_icon.scss",
            "deltatech_website_category_icon/static/src/snippets/s_category_icon_grid/*",
        ],
        "website.website_builder_assets": [
            "deltatech_website_category_icon/static/src/website_builder/*",
        ],
        "web.assets_tests": [
            "deltatech_website_category_icon/static/tests/tours/*",
        ],
    },
    "development_status": "Alpha",
    "maintainers": ["dhongu"],
}
