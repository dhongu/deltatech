# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Warehouse Arrangement",
    "category": "Stock",
    "summary": "Manages warehouse locations, parallel to standard Odoo locations",
    "version": "14.0.0.1.0",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": [
        "stock",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/warehouse_location.xml",
        "views/product_template.xml",
        "views/stock_lot.xml",
        "views/stock_quant.xml",
    ],
    "development_status": "Beta",
    "installable": True,
}
