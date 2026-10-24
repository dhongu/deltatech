# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
{
    "name": "MRP BoM Alternative Components",
    "summary": "Alternative components on BoM lines, substituted on manufacturing orders",
    "version": "20.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Manufacturing",
    "depends": ["mrp"],
    "license": "OPL-1",
    "data": [
        "security/ir.access.csv",
        "views/mrp_bom_line_alternative_views.xml",
        "views/mrp_bom_views.xml",
        "views/mrp_production_views.xml",
        "views/stock_move_views.xml",
        "views/res_config_settings_views.xml",
        "wizard/mrp_bom_alternative_substitute_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
