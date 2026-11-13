# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

{
    "name": "IAP Services for Odoo Online",
    "summary": "Use Terrabit services (credits, activation, buy credits) from data-only modules; importable on Odoo Online",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Hidden/Tools",
    "depends": ["base_automation"],
    "license": "LGPL-3",
    "data": [
        "data/ir_model_data.xml",
        "security/ir.model.access.csv",
        "data/ir_actions_server_data.xml",
        "data/base_automation_data.xml",
        "views/x_iap_online_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Alpha",
    "consultant_sheet": "full",
    "maintainers": ["dhongu"],
}
