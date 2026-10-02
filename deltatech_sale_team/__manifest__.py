# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Sale Team Access",
    "summary": "Sale Team Access",
    "version": "20.0.1.0.3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "depends": ["sales_team", "account", "stock", "sale_stock"],
    "license": "OPL-1",
    "data": [
        "security/sales_team_security.xml",
        "security/ir.access.csv",
        "views/sale_team_view.xml",
    ],
    "development_status": "Production/Stable",
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
}
