# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Vendor Products",
    "summary": "Vendor products",
    "version": "15.0.1.0.3",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Warehouse",
    "depends": ["product", "purchase"],
    "license": "OPL-1",
    "data": [
        "wizard/vendor_product_import_view.xml",
        "views/vendor_product_view.xml",
        "views/vendor_info_view.xml",
        "security/ir.model.access.csv",
    ],
    "qweb": [],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
