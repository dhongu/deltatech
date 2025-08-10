# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Purchase XLS - Enhanced",
    "summary": "Enhanced list view for purchase orders with vendor pricelist integration",
    "author": "Terrabit, Dorin Hongu, Enhanced by Custom Development",
    "version": "17.0.2.0.0",
    "license": "AGPL-3",
    "website": "https://www.terrabit.ro",
    "category": "Purchase",
    "depends": ["purchase_stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_order_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
