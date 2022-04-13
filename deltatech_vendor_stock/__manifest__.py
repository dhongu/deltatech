# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Vendor Stock",
    "summary": "Vendor stock availability",
    "version": "15.0.1.0.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": ["product", "sale_stock","deltatech_stock_inventory"],
    "license": "LGPL-3",
    "data": ["views/product_supplierinfo_view.xml", "views/sale_view.xml"],
    "qweb": ["static/src/xml/qty.xml"],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
