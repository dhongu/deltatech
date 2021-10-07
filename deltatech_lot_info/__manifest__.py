# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Serial/Lot Info",
    "summary": "Adds more info on product lot/serial number",
    "version": "14.0.1.0.0",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Administration",
    # "depends": ["web", "base", "stock", "deltatech_product_extension"],
    "depends": ["stock"],
    "license": "AGPL-3",
    "images": ["static/description/main_screenshot.png"],
    "data": [
        "views/stock_production_lot.xml",
        "security/ir.model.access.csv"
    ],
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
