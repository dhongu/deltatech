# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech UoM UNECE Codes",
    "summary": "Editable UNECE Rec 20/21 code on each unit of measure",
    "version": "19.0.1.0.0",
    "author": "Terrabit,Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Administration",
    "depends": ["account"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "data/uom_unece_code_data.xml",
        "data/uom_uom_data.xml",
        "views/uom_unece_code_views.xml",
        "views/uom_uom_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
