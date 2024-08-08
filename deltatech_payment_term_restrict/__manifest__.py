# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Payment Term Restrict",
    "summary": "Restricts payment terms change for certain users",
    "version": "16.0.0.0.1",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Base",
    "depends": ["account", "sale"],
    "license": "OPL-1",
    "data": [
        "security/security_groups.xml",
        "views/account_move.xml",
        "views/sale_order.xml",
        "views/res_partner.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
