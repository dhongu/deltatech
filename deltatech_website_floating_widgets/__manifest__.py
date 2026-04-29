# © 2024 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Website Floating Widgets",
    "version": "18.0.0.0.0",
    "category": "Website",
    "summary": "Floating widgets on the right side of the website",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": ["website"],
    "data": [
        "security/ir.model.access.csv",
        "views/website_floating_widget_views.xml",
        "views/website_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_website_floating_widgets/static/src/scss/floating_widgets.scss",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["VoicuStefan2001"],
}
