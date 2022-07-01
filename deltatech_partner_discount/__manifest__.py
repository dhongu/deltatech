# ©  2020 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech partner discount",
    "summary": "Creates a discount field on partner and alerts the user on invoice",
    "version": "15.0.1.0.0",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Sale",
    "depends": ["sale", "account"],
    "license": "LGPL-3",
    "data": [
        "views/res_partner.xml",
        "views/account_move.xml",
        "security/groups.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
