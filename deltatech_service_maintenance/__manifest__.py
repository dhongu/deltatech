# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Services Maintenance",
    "summary": "Services Maintenance",
    "version": "14.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Maintenance",
    "depends": [
        "deltatech_service",
        "deltatech_service_equipment",
        # "deltatech_service_history",
        "deltatech_procurement",
        "sale",
        "stock",
    ],
    "license": "AGPL-3",
    "data": [
        "security/service_security.xml",
        "data/data.xml",
        "views/service_notification_view.xml",
        "views/service_order_view.xml",
        "views/service_plan_view.xml",
        "views/service_equipment_view.xml",
        "views/stock_view.xml",
        "views/sale_view.xml",
        "security/ir.model.access.csv",
    ],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
