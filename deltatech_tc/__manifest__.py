# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

{
    "name": "Terrabit Connect - Base",
    "summary": "Base for Terrabit Connect: station registry, outbound job queue, REST endpoints (X-Station-Key) and HTTP calls into the customer's local network.",
    "version": "19.0.1.1.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Technical",
    # `bus.bus._sendone()` (notificări către manageri) e definit în `bus`.
    "depends": ["base", "bus"],
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
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
