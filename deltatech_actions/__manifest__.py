# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    "images": ["static/description/main_screenshot.png"],
    "name": "Deltatech Actions",
    "category": "Other",
    "summary": "Cleaning and other actions",
    "version": "19.0.0.0.9",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "license": "OPL-1",
    "depends": [
        "account_edi",
        "sale",
        "product",
        "stock",
    ],
    "data": [
        "data/ir_cron_data.xml",
    ],
    "development_status": "Beta",
    "installable": True,
}
