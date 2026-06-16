# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Raport PRN",
    "summary": "Raport PRN",
    "version": "18.0.1.1.0",
    "category": "Stock",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["web", "base_setup"],
    "license": "LGPL-3",
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Mature",
    "maintainers": ["dhongu"],
    "assets": {"web.assets_backend": ["deltatech_report_prn/static/src/js/action_manager.esm.js"]},
}
