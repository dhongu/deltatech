# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Services Maintenance Agreement",
    "summary": "Services Maintenance",
    "version": "15.0.1.0.4",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Services/Maintenance",
    "depends": [
        "deltatech_service_maintenance",
        "deltatech_service_equipment",
        "deltatech_service_agreement",
    ],
    "license": "OPL-1",
    "data": [
        "views/service_notification_view.xml",
        "views/service_order_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
