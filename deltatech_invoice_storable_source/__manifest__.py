# © 2026 Terrabit
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Invoice Storable Products Only from Orders",
    "summary": "Block posting invoices with storable products that do not come from a sale or purchase order",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "support": "support@terrabit.ro",
    "category": "Accounting/Accounting",
    "depends": ["sale_stock", "purchase_stock"],
    "license": "OPL-1",
    "consultant_sheet": "full",
    "data": ["views/res_config_settings_views.xml"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
