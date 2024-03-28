# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Services Equipment Base",
    "summary": "Service Equipment Management",
    "version": "17.0.1.1.4",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Equipment",
    "depends": ["deltatech_service_base", "product"],
    "license": "OPL-1",
    "data": [
        "data/data.xml",
        "security/service_security.xml",
        "security/ir.model.access.csv",
        "views/service_location_view.xml",
        "views/service_equipment_view.xml",
        "views/service_meter_view.xml",
        "views/service_config_view.xml",
        "wizard/enter_readings_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
