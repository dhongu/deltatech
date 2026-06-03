# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "name": "Sale Return Cause",
    "summary": "Return Cause",
    "version": "19.0.0.0.7",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "depends": ["sale"],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter_data.xml",
        "data/sale_return_cause_data.xml",
        "views/sale_order_view.xml",
        "views/sale_return_cause_view.xml",
        "views/sale_report_view.xml",
        "data/ir_cron_data.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
