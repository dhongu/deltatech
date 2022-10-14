# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Queue Job",
    "summary": "Queue Job using Crone",
    "version": "16.0.2.0.2",
    "author": "Terrabit, Dorin Hongu, Camptocamp,ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",
    "category": "Warehouse",
    "depends": ["base", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/queue_job_views.xml",
        "views/queue_job_menus.xml",
        "data/ir_cron_data.xml",
        "wizards/queue_jobs_to_done_views.xml",
        "wizards/queue_requeue_job_views.xml",
    ],
    "license": "LGPL-3",
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
