# ©  2026 Terrabit
# Based on the MD Trade customer analysis modules, © 2026 MD Trade Concept SRL
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Customer Segment",
    "summary": "Nightly per-customer buying rhythm, sales, overdue balance and portfolio segment",
    "version": "19.0.1.0.0",
    "author": "Terrabit, Dorin Hongu, MD Trade Concept SRL",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Sales/Sales",
    "depends": ["sale", "account"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/customer_segment_views.xml",
        "views/customer_segment_config_views.xml",
        "views/menus.xml",
    ],
    "post_init_hook": "post_init_hook",
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
