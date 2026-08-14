# ©  2008-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Website Searchbar Optimization",
    "category": "Website",
    "summary": "Reduce autocomplete requests by increasing debounce and adding minimum term length",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["website"],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_searchbar/static/src/js/searchbar.esm.js",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
