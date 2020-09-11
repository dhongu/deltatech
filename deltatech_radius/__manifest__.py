# ©  2018 Deltatech
# See README.rst file on addons root folder for license details
# Authors: João Figueira <jjnf@communities.pt>


{
    "name": "Radius Interface",
    "version": "12.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",
    "category": "Generic Modules/Base",
    "depends": ["account"],
    "license": "LGPL-3",
    "data": [
        "security/radius_security.xml",
        "security/ir.model.access.csv",
        "views/radius_view.xml",
        "views/res_partner_view.xml",
        "wizard/radius_disconnect_view.xml",
    ],
    "demo": ["data/radius_data.xml"],
    "images": ["images/main_screenshot.png"],
    "installable": True,
}
