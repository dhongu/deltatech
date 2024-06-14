# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Purchase Price History",
    "summary": "View minim, maxim and average purchase price from the last 12 months in product template",
    "version": "15.0.0.0.1",
    "author": "Terrabit, Dan Stoica",
    "license": "OPL-1",
    "website": "https://www.terrabit.ro",
    "category": "Purchase",
    "depends": ["purchase"],
    "data": [
        "views/product_template.xml",
        "data/ir_cron.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
