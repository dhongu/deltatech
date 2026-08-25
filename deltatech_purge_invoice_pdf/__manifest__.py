# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Purge Invoice PDF Attachments",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Delete auto-generated invoice PDF attachments to reclaim filestore space",
    "category": "Administration",
    "depends": ["account"],
    "data": [
        "data/ir_server_action.xml",
        "data/ir_cron.xml",
    ],
    "license": "OPL-1",
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
