# © 2026 Deltatech
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Purchase Create Bill Button",
    "summary": "Restores the one-click Create Bill button on the purchase order form and list, plus the vendor reference copy",
    "version": "19.0.1.1.0",
    "category": "Purchases",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["purchase"],
    "license": "LGPL-3",
    "data": ["views/purchase_view.xml"],
    "assets": {
        "web.assets_backend": [
            "deltatech_purchase_create_bill_button/static/src/views/purchase_listview.xml",
        ],
    },
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
