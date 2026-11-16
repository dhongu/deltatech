# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Transfer Product Images",
    "version": "20.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "consultant_sheet": "simple",
    "website": "https://www.terrabit.ro",
    "summary": "Product image on transfer lines, delivery slip and picking operations report",
    "category": "Inventory/Inventory",
    "depends": ["stock"],
    "data": [
        "views/stock_picking_view.xml",
        "views/res_config_view.xml",
        "views/report_templates.xml",
    ],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
