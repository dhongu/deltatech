# ©  2018 Terrabit
# See README.rst file on addons root folder for license details

{
    "name": "List View Extension",
    "summary": "List View Extension",
    "version": "15.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules",
    "depends": ["web"],
    "license": "LGPL-3",
    "data": [
        # "views/assets.xml"
    ],
    "qweb": ["static/src/xml/*.xml"],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "assets": {
        "web.assets_backend": [
            "/deltatech_list/static/src/js/list_renderer.js",
            "/deltatech_list/static/src/js/list_view.js",
            "/deltatech_list/static/src/js/list_controller.js"
        ]
    }
}
