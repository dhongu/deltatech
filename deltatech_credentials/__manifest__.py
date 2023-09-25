# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Credentials",
    "summary": "Manage credentials for external services",
    "version": "16.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Administration",
    "depends": ["base"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "views/access_credentials_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
