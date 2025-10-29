# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Website City",
    "category": "Website/Website",
    "summary": "City extension",
    "version": "19.0.1.1.1",
    "author": "Terrabit, Dorin Hongu",
    "support": "odoo@terrabit.ro",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "depends": ["portal", "website_sale", "base_address_extended"],
    "data": [
        "views/templates.xml",
        "data/ir_model_fields.xml",
    ],
    # "price": 10.00,
    # "currency": "EUR",
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_city/static/src/interactions/address.esm.js",
        ],
        "web.assets_tests": [
            "deltatech_website_city/static/tests/tours/address_city_zip.tour.esm.js",
        ],
    },
}
