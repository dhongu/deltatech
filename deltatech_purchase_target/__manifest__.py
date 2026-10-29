# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Purchase Targets by Manufacturer",
    "summary": "Quarterly purchase targets per manufacturer and eCommerce category, achieved vs target",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Purchase",
    "depends": [
        "purchase",
        "website_sale",
        "deltatech_product_extension",
        "deltatech_sale_margin",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/purchase_target_security.xml",
        "views/purchase_target_views.xml",
        "views/purchase_target_line_views.xml",
        "views/purchase_report_views.xml",
        "views/menu.xml",
    ],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
