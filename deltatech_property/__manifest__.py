# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Property Management",
    "version": "12.0.1.0.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Property",
    "depends": ["mail", "maintenance"],
    "license": "AGPL-3",
    "data": [
        "views/property_menu_view.xml",
        "views/property_config_view.xml",
        "views/property_land_view.xml",
        "views/property_building_view.xml",
        "views/property_room_view.xml",
        "data/data.xml",
        # "data/res.country.state.csv",
        "security/ir.model.access.csv",
    ],
    "application": True,
    "images": ["static/description/main_screenshot.png", "static/description/main_screenshot.svg"],
    "installable": True,
    "development_status": "stable",
    "maintainers": ["dhongu"],
}
