# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


{
    "name": "Terrabit - Record Type",
    "summary": "Manage multiple record types",
    "version": "18.0.1.1.11",
    "author": "Terrabit, Voicu Stefan",
    "website": "https://www.terrabit.ro",
    "category": "Generic Modules/Other",
    "depends": [
        "sale",
        "sale_stock",
        "purchase",
    ],
    "license": "OPL-1",
    "data": [
        "security/record_type_security.xml",
        "views/record_type_view.xml",
        "views/purchase_view.xml",
        "views/sale_view.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/account_move_view.xml",
    ],
    # "demo": [
    #     "data/demo_data.xml",
    # ],
    "development_status": "Mature",
    "images": ["static/description/main_screenshot.png"],
    "maintainers": ["VoicuStefan2001"],
}
