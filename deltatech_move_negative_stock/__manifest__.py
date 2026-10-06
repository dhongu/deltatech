# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Replenish negative stock",
    "summary": "Refill negative stock from another location in one click",
    "version": "18.0.1.1.2",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "support": "support@terrabit.ro",
    "category": "Inventory/Inventory",
    "depends": ["stock"],
    "license": "OPL-1",
    "data": [
        "views/stock_picking_view.xml",
        "data/mail_data.xml",
        "data/ir_cron.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
