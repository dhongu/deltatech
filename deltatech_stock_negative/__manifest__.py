# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "No Negative Stock",
    "summary": "Block transfers that would take stock below zero",
    "version": "19.0.2.0.12",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "support": "support@terrabit.ro",
    "category": "Inventory/Inventory",
    "depends": ["stock"],
    "license": "OPL-1",
    "data": ["views/res_config_view.xml", "views/stock_location_view.xml"],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
