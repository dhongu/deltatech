# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Vendor Stock",
    "summary": "Vendor stock availability",
    "version": "18.0.1.0.5",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": [
        "product",
        "sale_stock",
        # "deltatech_stock_inventory"
    ],
    "license": "OPL-1",
    "data": ["views/product_supplierinfo_view.xml", "views/sale_view.xml"],
    "assets": {
        "web.assets_backend": [
            "deltatech_vendor_stock/static/src/xml/**/*",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
