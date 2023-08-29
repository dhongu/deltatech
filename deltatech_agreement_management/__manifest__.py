# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Agreement Management",
    "summary": "Manage agreements numbers, date, state",
    "version": "15.0.0.0.1",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Services/Agreement",
    "depends": ["base", "mail", "deltatech_service_base"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "views/agreement.xml",
        "views/res_partner.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "application": False,
    "development_status": "Production/Stable",
    "maintainers": ["danila12"],
}
