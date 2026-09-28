# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "KPI Cards",
    "summary": "A reusable band of KPI cards for backend views, each card toggling a search filter",
    "version": "20.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Hidden/Tools",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "deltatech_web_kpi_cards/static/src/kpi_cards/*",
        ],
        "web.assets_unit_tests": [
            "deltatech_web_kpi_cards/static/tests/**/*",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
