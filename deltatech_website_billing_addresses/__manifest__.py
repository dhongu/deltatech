# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Website Billing Addresses",
    "category": "Website/Website",
    "summary": "ebsite Billing Addresses",
    "version": "15.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "license": "AGPL-3",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale"],
    "data": ["views/templates.xml"],
    "images": ["static/description/main_screenshot.png"],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_billing_addresses/static/src/js/billing_addresses.js",
        ],
    },
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
