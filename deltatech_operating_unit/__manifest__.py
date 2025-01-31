# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


{
    "name": "Terrabit - Operating Unit",
    "summary": "Manage multiple operating units",
    "version": "17.0.0.0.0",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Other",
    "depends": [
        "base",
        "account",
        "deltatech_sale_store",
    ],
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "views/operating_unit_view.xml",
        "views/account_journal.xml",
        "wizard/sale_store_wizard.xml",
    ],
    "development_status": "Alpha",
    "images": ["static/description/main_screenshot.png"],
    "maintainers": ["VoicuStefan2001"],
}
