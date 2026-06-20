# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

{
    "name": "Terrabit Connect - Base",
    "summary": "Base for Terrabit Connect: station registry, outbound job queue and REST endpoints (X-Station-Key).",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Technical",
    "depends": ["base"],
    "license": "OPL-1",
    "data": [
        "security/deltatech_tc_security.xml",
        "security/ir.model.access.csv",
        "views/deltatech_tc_station_views.xml",
        "views/deltatech_tc_job_views.xml",
        "views/menus.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
