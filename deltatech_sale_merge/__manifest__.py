# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Sale Merge",
    "summary": "Merge several quotations of the same customer into one",
    "version": "20.0.1.0.0",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["sale"],
    "license": "LGPL-3",
    "consultant_sheet": "full",
    "data": ["views/sale_order_views.xml", "wizard/sale_order_merge_views.xml", "security/ir.access.csv"],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
