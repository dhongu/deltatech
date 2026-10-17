# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "Website Searchbar Typing Examples",
    "category": "Website",
    "summary": "The search box placeholder types example searches, one after another",
    "version": "20.0.1.1.0",
    "license": "LGPL-3",
    "author": "Terrabit, Dorin Hongu",
    "support": "odoo@terrabit.ro",
    "website": "https://www.terrabit.ro",
    "depends": ["website"],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_searchbar_typing/static/src/interactions/searchbar_typing.esm.js",
        ],
        "web.assets_unit_tests_setup": [
            "deltatech_website_searchbar_typing/static/src/interactions/searchbar_typing.esm.js",
        ],
        "website.website_builder_assets": [
            "deltatech_website_searchbar_typing/static/src/website_builder/*",
        ],
        "web.assets_unit_tests": [
            "deltatech_website_searchbar_typing/static/tests/**/*.test.js",
        ],
    },
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
