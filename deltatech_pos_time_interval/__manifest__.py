# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "POS Order Time Interval",
    "summary": "Searching pos order report to compare 2 time intervals",
    "version": "18.0.0.0.0",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "category": "Point of Sale",
    "depends": ["point_of_sale"],
    "license": "LGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "wizard/time_interval_search_wizard.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
