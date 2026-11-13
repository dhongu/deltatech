# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "Side Panel",
    "summary": "A side panel with the details of the selected record, for kanban and list views",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Hidden/Tools",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [],
    "demo": ["demo/demo_views.xml"],
    "assets": {
        "web.assets_backend": [
            "deltatech_web_side_panel/static/src/side_panel/*",
        ],
        "web.assets_unit_tests": [
            "deltatech_web_side_panel/static/tests/**/*",
        ],
    },
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
