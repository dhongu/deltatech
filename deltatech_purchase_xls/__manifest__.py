# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Purchase XLS",
    "summary": "Import/export purchase line from/to Excel",
    "author": "Terrabit, Dorin Hongu",
    "version": "18.0.1.0.7",
    "license": "AGPL-3",
    "website": "https://www.terrabit.ro",
    "category": "Purchase",
    "depends": ["purchase_stock"],
    "data": [
        "wizard/import_purchase_line_view.xml",
        "wizard/export_purchase_line_view.xml",
        "security/ir.model.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
