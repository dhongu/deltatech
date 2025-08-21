# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Test System",
    "summary": "Set system status: test or production",
    "version": "17.0.0.0.6",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Tools",
    "depends": ["web"],
    "license": "OPL-1",
    "data": [
        # "views/templates.xml",
        "views/res_config_settings_view.xml",
        "views/ir_module_module_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
    "auto_install": False,
}
