# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech  Queue Job Enhancements",
    "summary": "Deltatech Queue Job",
    "author": "Terrabit, Dorin Hongu",
    "version": "18.0.1.3.0",
    "license": "AGPL-3",
    "website": "https://www.terrabit.ro",
    "category": "Others",
    "depends": ["queue_job", "queue_job_cron_jobrunner"],
    "data": [
        "views/queue_job_views.xml",
        "views/res_config_settings_views.xml",
        "data/ir_config_parameter.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["dhongu"],
}
