# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Services Maintenance Plan",
    "summary": "Services Maintenance",
    "version": "16.0.1.0.4",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Maintenance",
    "depends": [
        "deltatech_service_base",
        "deltatech_service_maintenance",
        "deltatech_service_equipment",  # se utilizeaza planificarea pe contoare
    ],
    "license": "AGPL-3",
    "data": [
        "security/service_security.xml",
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/service_plan_view.xml",
        "views/service_equipment_view.xml",
    ],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
