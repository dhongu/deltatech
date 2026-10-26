# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Import Lines in Transfers and Inventory",
    "summary": "Load transfer moves and inventory counts from an XLSX, XLS, CSV or TXT file",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Inventory/Inventory",
    "depends": ["deltatech_import_lines", "stock"],
    "license": "OPL-1",
    "data": ["views/stock_picking_view.xml", "views/stock_quant_view.xml", "wizard/import_lines_wizard_view.xml"],
    "images": ["static/description/main_screenshot.png"],
    "auto_install": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
