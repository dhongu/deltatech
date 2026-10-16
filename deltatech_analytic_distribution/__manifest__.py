# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "Analytic Distribution Enforcer",
    "category": "Accounting",
    "summary": "Block posting vendor bills until every line is 100% analytically distributed",
    "version": "20.0.0.0.7",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": [
        "account",
    ],
    "data": [
        "views/res_config_view.xml",
    ],
    "development_status": "Beta",
    "installable": True,
}
