# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Import Document Lines",
    "summary": "Load document lines from an XLSX, XLS, CSV or TXT file, with column mapping and preview",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Productivity",
    "depends": ["product", "base_import"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "security/import_lines_security.xml",
        "views/import_lines_mapping_view.xml",
        "wizard/import_lines_wizard_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
