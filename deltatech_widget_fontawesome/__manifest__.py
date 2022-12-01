# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "FontAwesome Widget",
    "summary": "Font Awesome Widget",
    "version": "15.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "AGPL-3",
    "category": "Generic Modules",
    "depends": ["web"],
    "data": [],
    "installable": True,
    "qweb": ["static/src/xml/*.xml"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
    "assets": {
        "web.assets_backend": ["deltatech_widget_fontawesome/static/src/js/fontawesome.js"],
    },
    "images": ["static/description/main_screenshot.png"],
}
