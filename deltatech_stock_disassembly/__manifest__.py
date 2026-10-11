# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Free Disassembly",
    "summary": "Disassembly report without bill of materials, with cost allocation",
    "version": "20.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Inventory/Inventory",
    "depends": ["stock_account"],
    "license": "OPL-1",
    "data": [
        "security/ir.access.csv",
        "data/ir_sequence.xml",
        "report/report_stock_disassembly.xml",
        "views/stock_disassembly_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
