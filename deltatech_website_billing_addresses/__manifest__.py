# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Website Billing Addresses",
    "category": "Website/Website",
    "summary": "Website Billing Addresses",
    "version": "16.0.1.2.6",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale"],
    "data": [
        "views/templates.xml",
        "views/addresses_portal_templates.xml",
        "views/res_partner_view.xml",
        "security/base_security.xml",
        "views/auth_signup.xml",
        "wizard/create_billing_address.xml",
        "security/ir.model.access.csv",
    ],
    "price": 10.00,
    "currency": "EUR",
    "images": ["static/description/main_screenshot.png"],
    "css": ["static/src/scss/override.scss"],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_billing_addresses/static/src/js/billing_addresses.js",
        ],
    },
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
