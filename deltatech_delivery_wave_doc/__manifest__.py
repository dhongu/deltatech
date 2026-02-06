# © 2026 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Vendor Delivery Document to Wave",
    "version": "17.0.1.0.0",
    "summary": "Document furnizor cu linii ce generează Batch/Wave pe recepții existente",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "LGPL-3",
    "depends": ["mail", "stock", "stock_picking_batch", "purchase_stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/delivery_vendor_document_views.xml",
    ],
    "installable": True,
    "development_status": "Beta",
}
