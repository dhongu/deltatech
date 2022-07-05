# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Payment",
    "summary": "Payment button in sale order",
    "version": "15.0.1.0.2",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["sale", "payment"],
    "license": "LGPL-3",
    "data": ["views/sale_view.xml", "wizard/sale_confirm_payment_view.xml", "security/ir.model.access.csv"],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
