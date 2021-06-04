# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Simple MRP",
    "summary": "Simple production",
    "version": "14.0.1.0.0",
    "author": "Terrabit, Dorin Hongu, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Manufacturing",
    "depends": ["stock", "sale"],
    "license": "LGPL-3",
    "data": ["wizard/mrp_simple_view.xml", "security/ir.model.access.csv", "views/sale_order.xml"],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
