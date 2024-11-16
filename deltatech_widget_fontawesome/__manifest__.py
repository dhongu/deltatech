# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "FontAwesome Widget",
    "summary": "Font Awesome Widget",
    "version": "18.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Generic Modules",
    "depends": ["web"],
    "data": [],
    "installable": True,
    "qweb": ["static/src/xml/*.xml"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
    "assets": {
        "web.assets_backend": [
            "deltatech_widget_fontawesome/static/src/js/field_fontawesome.esm.js",
            "deltatech_widget_fontawesome/static/src/js/field_fontawesome.xml",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
}
