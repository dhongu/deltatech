# ©  2023 Deltatech - Dorin Hongu
# See README.rst file on addons root folder for license details
{
    "name": "eCommerce Attribute Filter Snippet",
    "category": "Website",
    "summary": "eCommerce Attribute Values Filter Snippet",
    "images": ["static/description/main_screenshot.png"],
    "version": "15.0.1.0.4",
    "author": "Terrabit, Dorin Hongu",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "depends": ["website", "website_sale"],
    "data": ["views/snippets.xml"],
    "assets": {
        "web.assets_frontend": ["deltatech_website_snippet_attribute_filter/static/src/js/attribute_filter.js"],
        "website.assets_wysiwyg": [
            "deltatech_website_snippet_attribute_filter/static/src/js/attribute_filter_editor.js"
        ],
    },
    "qweb": ["static/src/xml/*.xml"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
