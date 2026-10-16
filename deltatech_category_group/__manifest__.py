# ©  2008-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

{
    "name": "Internal Category Groups",
    "summary": "Groups for internal categories",
    "version": "20.0.0.0.7",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Other",
    "depends": [
        "deltatech_sale_commission",
    ],
    "license": "OPL-1",
    "data": [
        "security/security.xml",
        "views/product_category.xml",
        "views/category_types_views.xml",
        "views/stock_quant.xml",
        "report/sale_margin_report.xml",
        "report/account_invoice_report.xml",
        "security/ir.access.csv",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
