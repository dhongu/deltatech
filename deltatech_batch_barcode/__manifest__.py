# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Batch Transfer Barcode",
    "summary": "Batch Transfer Barcode",
    "version": "14.0.0.0.1",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",
    "category": "Inventory/Inventory",
    "external_dependencies": {"python": []},
    "depends": ["stock_barcode_picking_batch"],
    "data": [
        "views/stock_picking_batch.xml",
    ],
    "license": "LGPL-3",
    "development_status": "Beta",
    "images": ["static/description/main_screenshot.png"],
    "maintainers": ["dhongu"],
}
