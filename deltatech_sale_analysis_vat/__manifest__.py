# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Sale Analysis by VAT",
    "summary": "VAT rate dimension in Invoice Analysis and Point of Sale Analysis",
    "version": "18.0.1.0.2",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "depends": ["account", "point_of_sale"],
    "license": "OPL-1",
    "data": [
        "views/account_invoice_report_views.xml",
        "views/pos_order_report_views.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
