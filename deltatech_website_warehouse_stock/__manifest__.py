# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Warehouse Stock",
    "category": "Website",
    "summary": "Stock availability per warehouse on the eCommerce product page",
    "version": "20.0.0.0.5",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "depends": ["website", "website_sale_stock"],
    "data": [
        "views/website_sale_stock_templates.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_warehouse_stock/static/src/scss/warehouse_stock.scss",
            "deltatech_website_warehouse_stock/static/src/interactions/warehouse_stock_selector.esm.js",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "license": "OPL-1",
    "development_status": "Alpha",
    "maintainers": ["VoicuStefan2001"],
}
