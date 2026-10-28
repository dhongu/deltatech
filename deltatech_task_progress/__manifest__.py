# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
{
    "name": "Task Progress",
    "summary": "Run a long task step by step, several steps at a time, in a progress dialog",
    "version": "19.0.1.1.2",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "LGPL-3",
    "category": "Technical",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "deltatech_task_progress/static/src/task_progress/*",
        ],
        "web.assets_unit_tests": [
            "deltatech_task_progress/static/tests/*",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
