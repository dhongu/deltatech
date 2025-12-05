# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Website VAT Validation",
    "summary": "VAT Validation with Romanian CUI requirements and ANAF auto-fill",
    "version": "18.0.1.1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Generic Modules",
    "depends": ["website_sale", "phone_validation", "portal"],
    "data": [
        "views/website_sale_templates.xml",
        "views/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_vat_validation/static/src/scss/website_vat_validation.scss",
            "deltatech_website_vat_validation/static/src/js/website_vat_validation.js",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
