# ©  2023-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Warranty",
    "summary": "Warranty field in product, report for sale order",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "depends": ["sale"],
    "license": "OPL-1",
    "data": [
        "views/sale_order.xml",
        "views/product_template.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu", "danila12"],
}
