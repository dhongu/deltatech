# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "Kaizen Improvement Projects",
    "summary": "Improvement projects tied to a measured loss: baseline, 5 Why, Ishikawa, actions and savings",
    "version": "20.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "LGPL-3",
    "category": "Manufacturing/Quality",
    "depends": ["mail"],
    "data": [
        "security/kaizen_security.xml",
        "security/ir.access.csv",
        "data/ir_sequence_data.xml",
        "views/kaizen_project_views.xml",
        "views/kaizen_menu.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
