# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

# todo: o parte din functionalitatile acestui modul sunt in deltatech_website_stock_availability
{
    "name": "eCommerce Sale Stock extension",
    "category": "Website",
    "summary": "eCommerce extension",
    "version": "13.0.2.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "LGPL-3",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale_stock"],
    "data": [
        "views/product_view.xml",
        "views/templates.xml",
        "views/website_keyword_view.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
