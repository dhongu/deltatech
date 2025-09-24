# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "MRP Concentration",
    "summary": "MRP Concentration",
    "version": "18.0.1.0.1",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Production",
    "depends": ["base", "mrp", "stock", "sale", "product"],
    "data": [
        "views/mrp_bom_view.xml",
        "views/mrp_production_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
