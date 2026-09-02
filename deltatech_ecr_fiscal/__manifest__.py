# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "ECR Fiscal Audit Fields",
    "summary": "Common fiscal printer audit fields shared by POS, invoicing and localizations",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",
    "category": "Sales/Point of Sale",
    "depends": ["point_of_sale", "account"],
    "license": "OPL-1",
    "price": 0.00,
    "currency": "EUR",
    "pre_init_hook": "pre_init_hook",
    "development_status": "Production/Stable",
    "installable": True,
    "application": False,
    "hidden": True,
}
