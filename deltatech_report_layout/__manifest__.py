# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Report Layout",
    "summary": "Eight extra PDF report layouts; data-only, importable on Odoo Online",
    "version": "20.0.1.3.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "category": "Manufacturing",
    "depends": ["web"],
    "data": [
        "views/report_template_style1.xml",
        "views/report_template_style2.xml",
        "views/report_template_style3.xml",
        "views/report_template_style4.xml",
        "views/report_template_style5.xml",
        "views/report_template_style6.xml",
        "views/report_template_style7.xml",
        "views/report_template_style8.xml",
        "data/report_layout.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "deltatech_report_layout/static/src/scss/report_style1.scss",
            "deltatech_report_layout/static/src/scss/report_style2.scss",
            "deltatech_report_layout/static/src/scss/report_style3.scss",
            "deltatech_report_layout/static/src/scss/report_style4.scss",
            "deltatech_report_layout/static/src/scss/report_style5.scss",
            "deltatech_report_layout/static/src/scss/report_style6.scss",
            "deltatech_report_layout/static/src/scss/report_style7.scss",
            "deltatech_report_layout/static/src/scss/report_style8.scss",
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
    "installable": True,
}
