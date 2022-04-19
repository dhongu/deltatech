# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Website Billing Addresses",
    "category": "Website/Website",
    "summary": "Website Billing Addresses",
    "version": "14.0.1.0.6",
    "author": "Terrabit, Dorin Hongu",
    "license": "AGPL-3",
    "website": "https://www.terrabit.ro",
    "depends": ["website_sale"],
    "data": [
        "views/templates.xml",
        "views/addresses_portal_templates.xml",
        "views/res_partner_view.xml",
        "security/base_security.xml",
        "views/assets.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
