# ©  2025 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Image Optimizer",
    "version": "19.0.1.6.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Recompress oversized image attachments to reclaim filestore space",
    "category": "Administration",
    "depends": ["base"],
    "data": [
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
    ],
    "license": "OPL-1",
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
