# © 2024 Deltatech
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "Website Sale Attribute Filter",
    "version": "19.0.0.1.0",
    "category": "Website",
    "summary": "Filter attribute values based on displayed products",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": ["website_sale"],
    "data": [
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_sale_attribute_filter/static/src/interactions/attribute_filter_state.esm.js",
        ],
    },
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
