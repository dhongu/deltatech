# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Report Layout",
    "summary": "Customized report layouts ",
    "version": "18.0.0.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Manufacturing",
    "depends": ["web"],
    "data": ["views/report_template_style1.xml", "views/report_template_style2.xml", "data/report_layout.xml"],
    "assets": {
        "web.report_assets_common": [
            "deltatech_report_layout/static/src/**/*",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "installable": True,
}
