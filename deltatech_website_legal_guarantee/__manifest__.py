# © 2026 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "EU Legal Guarantee Notice",
    "version": "19.0.1.0.0",
    "category": "Website/Website",
    "summary": "Displays the EU harmonised notice on the legal guarantee of conformity on the website, in all EU languages",
    "author": "Terrabit, Dorin Hongu",
    "support": "odoo@terrabit.ro",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": ["website_sale"],
    "data": [
        "views/templates.xml",
        "views/national_ro.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
