# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Services Equipment Base",
    "summary": "Service Equipment Management",
    "version": "16.0.1.1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Equipment",
    "depends": ["deltatech_service_base", "product"],
    "license": "AGPL-3",
    "data": [
        "data/data.xml",
        "security/service_security.xml",
        "security/ir.model.access.csv",
        "views/service_equipment_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
