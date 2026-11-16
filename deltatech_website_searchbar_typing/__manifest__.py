# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "Website Searchbar Typing Examples",
    "category": "Website",
    "summary": "The search box placeholder types example searches, one after another",
    "version": "19.0.1.2.0",
    "license": "LGPL-3",
    "consultant_sheet": "full",
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
            "deltatech_website_searchbar_typing/static/src/website_builder/searchbar_typing_option.xml",
            "deltatech_website_searchbar_typing/static/src/website_builder/searchbar_typing_option_plugin.esm.js",
        ],
        "web.assets_unit_tests": [
            "deltatech_website_searchbar_typing/static/tests/searchbar_typing.test.js",
            "deltatech_website_searchbar_typing/static/tests/builder/searchbar_typing_option.test.js",
        ],
    },
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
