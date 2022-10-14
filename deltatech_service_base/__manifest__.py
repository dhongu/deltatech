# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Services Base",
    "summary": "Manage Services Base",
    "version": "16.0.2.0.4",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Agreement",
    "depends": ["product", "account"],
    "license": "AGPL-3",
    "data": [
        "security/service_security.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/service_cycle_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "application": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
