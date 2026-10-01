# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Replenish Negative Stock",
    "summary": "Refill negative stock from another location in one click",
    "version": "19.0.1.1.3",
    "author": "Terrabit, Dan Stoica",
    "website": "https://www.terrabit.ro",
    "support": "support@terrabit.ro",
    "category": "Inventory/Inventory",
    "depends": ["stock", "mail"],
    "license": "OPL-1",
    "data": [
        "views/stock_location_view.xml",
        "views/stock_picking_view.xml",
        "data/mail_data.xml",
        "data/ir_cron.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["danila12"],
}
