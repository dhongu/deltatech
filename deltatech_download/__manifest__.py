# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Download File",
    "version": "18.0.0.1.1",
    "author": "Terrabit,Dorin Hongu",
    "summary": "Generare fisier",
    "website": "https://www.terrabit.ro",
    "category": "Base",
    "depends": ["web"],
    "license": "OPL-1",
    "data": [
        "views/ir_action_report_view.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["images/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
    "assets": {
        "web.assets_backend": ["deltatech_download/static/src/js/action_manager.esm.js"],
    },
}
