# ©  2026-now Terrabit
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Document Weight",
    "summary": "Net and gross weight and volume per line and in total on quotations and invoices",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "consultant_sheet": "simple",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "depends": ["sale", "account"],
    "data": [
        "views/product_template_views.xml",
        "views/res_config_settings_views.xml",
        "views/sale_order_report.xml",
        "views/account_move_report.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
