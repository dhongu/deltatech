# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Refund Purchase",
    "summary": "Vendor credit notes for negative quantities",
    "version": "19.0.1.0.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Purchases",
    "depends": ["base", "account", "purchase_stock", "stock"],
    "price": 5.00,
    "currency": "EUR",
    "license": "LGPL-3",
    "data": ["views/account_invoice_view.xml"],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
