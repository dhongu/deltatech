# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Registry Office",
    "version": "11.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Document Management",
    "depends": ["document", "mail", "deltatech_contact"],
    "license": "LGPL-3",
    "data": [
        "wizard/solution_view.xml",
        "wizard/user_view.xml",
        "views/registry_office_view.xml",
        "data/data.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["images/main_screenshot.png"],
    "active": False,
    "installable": True,
    "application": True,
}
