# ©  2008-2022 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "List View Select Text (importable, Odoo Online)",
    "summary": "Select text in list views without opening the record; data-only, importable on Odoo Online",
    "version": "20.0.1.1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules",
    "depends": ["web"],
    "license": "OPL-1",
    "data": [],
    "images": ["static/description/main_screenshot.png"],
    "assets": {
        "web.assets_backend": [
            "deltatech_list_view/static/src/js/list_renderer.esm.js",
            "deltatech_list_view/static/src/js/static_list.esm.js",
        ],
        "web.assets_web_dark": ["deltatech_list_view/static/src/scss/style_dark.scss"],
        "web.assets_unit_tests": ["deltatech_list_view/static/tests/static_list_delete.test.js"],
    },
    "development_status": "Production/Stable",
}
