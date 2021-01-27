# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Promissory Note",
    "summary": "gestionare bilete la ordin",
    "version": "14.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Stock",
    "depends": ["account"],
    "license": "AGPL-3",
    "data": [
        "views/promissory_note_view.xml",
        "views/promissory_note_report.xml",
        "security/promissory_note_security.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["danila12"],
}
