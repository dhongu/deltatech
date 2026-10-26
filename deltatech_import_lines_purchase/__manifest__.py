# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Import Lines in Purchase Orders",
    "summary": "Load purchase order lines from an XLSX, XLS, CSV or TXT file, also by vendor product code",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Purchase",
    "depends": ["deltatech_import_lines", "purchase"],
    "license": "OPL-1",
    "data": ["views/purchase_order_view.xml"],
    "images": ["static/description/main_screenshot.png"],
    "auto_install": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
