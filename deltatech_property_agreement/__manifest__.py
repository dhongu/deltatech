# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Property Agreement",
    "version": "12.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Property",
    "depends": ["deltatech_property", "deltatech_service_equipment"],
    "license": "AGPL-3",
    "data": ["views/property_building_view.xml", "security/ir.model.access.csv"],
    "application": True,
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "stable",
    "maintainers": ["dhongu"],
}
