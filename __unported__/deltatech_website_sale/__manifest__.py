# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Sale Stock extension",
    "category": "Website",
    "summary": "eCommerce extension",
    "version": "13.0.3.0.0",
    "author": "Terrabit, Dorin Hongu",
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
}
