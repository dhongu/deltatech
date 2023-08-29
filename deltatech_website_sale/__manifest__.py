# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

# todo: o parte din functionalitatile acestui modul sunt in deltatech_website_stock_availability
{
    "name": "eCommerce Sale Stock extension",
    "category": "Website",
    "summary": "eCommerce extension",
    "version": "15.0.2.0.3",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale_stock"],
    "data": [
        "views/website_keyword_view.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_sale/static/src/scss/website_fix.scss",
        ],
    },
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
