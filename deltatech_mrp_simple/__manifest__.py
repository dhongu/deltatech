# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Simple MRP",
    "summary": "Simple production",
    "version": "15.0.1.0.5",
    "author": "Terrabit, Dorin Hongu, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "category": "Manufacturing",
    "depends": ["stock", "sale"],
    "license": "OPL-1",
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "views/mrp_simple_view.xml",
        "views/sale_order.xml",
        "wizard/add_multi_lines.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
