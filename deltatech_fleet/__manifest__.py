# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Fleet",
    "version": "17.0.1.0.0",
    "author": "Dorin Hongu, Terrabit",
    "website": "https://www.terrabit.ro",
    "category": "Human Resources/Fleet",
    "license": "OPL-1",
    "summary": "Vehicle, route, map sheet",
    "depends": ["fleet"],
    "data": [
        "data/fleet_data.xml",
        "views/fleet_fuel_view.xml",
        "views/fleet_view.xml",
        "views/fleet_sheet_view.xml",
        "views/fleet_report.xml",
        "views/report_map_sheet.xml",
        "wizard/fleet_dist_report_view.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
