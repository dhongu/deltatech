# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Margin",
    "summary": "Check price in sale order",
    "version": "17.0.1.0.5",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["sale_margin", "account", "stock_account"],
    "license": "OPL-1",
    "data": [
        "security/sale_security.xml",
        "views/sale_margin_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
