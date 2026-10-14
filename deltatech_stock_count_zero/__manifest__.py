# ©  Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details
{
    "name": "Stock Count Zero",
    "category": "Stock",
    "summary": "Set inventory line to 0 when empty count is requested",
    "version": "20.0.0.0.4",
    "license": "OPL-1",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "depends": ["stock"],
    "data": [
        "views/stock_request_count_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["VoicuStefan2001"],
}
