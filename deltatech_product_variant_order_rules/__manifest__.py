# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Create order rules for variants from template",
    "category": "Stock",
    "summary": "Will create order rules for all variants of a template with a wizard",
    "version": "17.0.0.0.0",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": ["stock", "purchase_stock", "sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/order_rules_details_view.xml",
        "views/product_template_view.xml",
    ],
    "development_status": "Beta",
    "installable": True,
}
