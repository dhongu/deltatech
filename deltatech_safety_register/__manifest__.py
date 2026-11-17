# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Safety Register",
    "summary": "Register of safety incidents, work accidents and near misses, with corrective actions and LTIFR",
    "version": "20.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Human Resources",
    "depends": ["base", "mail", "hr", "hr_attendance"],
    "data": [
        "security/security.xml",
        "security/ir.access.csv",
        "data/ir_sequence.xml",
        "views/safety_event_views.xml",
        "views/safety_action_views.xml",
        "wizard/safety_indicator_views.xml",
        "views/menu.xml",
    ],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
    "installable": True,
}
