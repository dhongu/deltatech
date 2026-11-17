# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details

{
    "name": "World Class Manufacturing Dashboard",
    "summary": "One dashboard for the ten WCM pillars: indicators, targets and traffic lights",
    "version": "20.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Manufacturing/Manufacturing",
    "depends": ["mrp", "maintenance", "quality", "stock"],
    "data": [
        "security/ir.access.csv",
        "data/wcm_pillar_data.xml",
        "data/wcm_indicator_data.xml",
        "views/wcm_pillar_views.xml",
        "views/wcm_indicator_views.xml",
        "views/wcm_menus.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
