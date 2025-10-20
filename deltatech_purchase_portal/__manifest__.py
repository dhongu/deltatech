# © 2025 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Purchase Portal",
    "summary": "Purchase order portal access for your vendors",
    "version": "18.0.1.0.1",
    "category": "Purchase",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "depends": ["purchase", "portal"],
    "license": "LGPL-3",
    "data": ["views/portal_templates.xml"],
    "assets": {
        "web.assets_frontend": [
            "deltatech_purchase_portal/static/src/js/purchase.esm.js",
        ],
    },
    "development_status": "Beta",
    "maintainers": ["danila12"],
    "images": ["static/description/main_screenshot.png"],
}
