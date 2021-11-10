# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Sale Team Access",
    "version": "12.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "depends": ["sales_team", "account", "stock", "sale_stock"],
    "license": "LGPL-3",
    "data": [
        "security/sales_team_security.xml",
        "views/sale_team_view.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
}
