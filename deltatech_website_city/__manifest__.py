# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Website City",
    "category": "Website/Website",
    "summary": "City extension",
    "version": "18.0.1.1.1",
    "author": "Terrabit, Dorin Hongu",
    "license": "LGPL-3",
    "website": "https://www.terrabit.ro",
    "depends": ["portal", "website_sale", "base_address_extended"],
    "data": [
        # "views/portal.xml",
        "views/website_address.xml",
        "data/ir_model_fields.xml",
    ],
    "price": 10.00,
    "currency": "EUR",
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_city/static/src/js/website_sale.esm.js",
            # "deltatech_website_city/static/src/js/portal.esm.js",  #todo in lucru
        ],
    },
}
