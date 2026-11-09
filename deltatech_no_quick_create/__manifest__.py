# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "No Quick Create",
    "summary": "Disable quick create in many2one fields; data-only, importable on Odoo Online",
    "version": "20.0.2.1.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Tools",
    "depends": ["base", "web"],
    "license": "OPL-1",
    "data": [],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
    "assets": {
        "web.assets_backend": [
            "deltatech_no_quick_create/static/src/js/fields.esm.js",
        ]
    },
}
