# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Simple MRP",
    "summary": "Simple production",
    "version": "15.0.1.0.2",
    "author": "Terrabit, Dorin Hongu, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Manufacturing",
    "depends": ["stock", "sale"],
    "license": "LGPL-3",
    "data": [
        "views/mrp_simple_view.xml",
        "security/ir.model.access.csv",
        "security/groups.xml",
        "data/ir_config_parameter.xml",
        "views/sale_order.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
