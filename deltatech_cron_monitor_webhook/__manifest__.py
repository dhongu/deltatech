{
    "name": "Deltatech Cron Monitor Webhook",
    "version": "18.0.1.0.0",
    "category": "Technical",
    "summary": "Run cron jobs from webhook",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["base", "mail", "web"],
    "data": [
        "views/ir_cron_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
    "development_status": "Beta",
}
