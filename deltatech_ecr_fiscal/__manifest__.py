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
    # Mature, nu Production/Stable: `deltatech_sale_store` este Mature, iar
    # `manifestoo check-dev-status` interzice dependența pe un modul cu statut mai jos.
    # Se justifică: modulul doar găzduiește definiții de câmpuri aflate în producție
    # de ani, mutate aici neschimbate.
    "development_status": "Mature",
    "installable": True,
    "application": False,
    "hidden": True,
}
