# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "SMS Custom Gateway",
    "summary": "Send Odoo SMS through your own 4Pay or Wapi account instead of IAP",
    "version": "20.0.1.0.3",
    "author": "Terrabit, Dorin Hongu, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Extra Tools",
    "depends": ["sms"],
    "external_dependencies": {"python": ["unidecode"]},
    "license": "OPL-1",
    "data": ["views/iap_views.xml"],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
