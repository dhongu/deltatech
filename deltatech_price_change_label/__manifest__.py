# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Price Change Labels",
    "summary": "Print product labels for the products of a price change document",
    "version": "19.0.1.0.3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "depends": ["deltatech_price_change", "deltatech_product_labels"],
    "license": "OPL-1",
    "data": ["views/product_price_change_view.xml", "views/report_shelf_label.xml"],
    "auto_install": True,
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
