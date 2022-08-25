# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Error Dialog",
    "version": "15.0.0.1.1",
    "author": "Terrabit,Dorin Hongu",
    "summary": "Error Dialog",
    "website": "https://www.terrabit.ro",
    "category": "Base",
    "depends": ["web", "web_enterprise"],
    "license": "LGPL-3",
    "data": [],
    "qweb": ["static/src/xml/error_dialog.xml"],
    "images": ["images/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
    "assets": {
        "web.assets_backend": ["deltatech_error_dialog/static/src/js/error_dialog.esm.js"],
        "web.assets_qweb": ["deltatech_error_dialog/static/src/xml/error_dialog.xml"],
    },
}
