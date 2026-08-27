# ©  2025 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Image Optimizer",
    "version": "19.0.1.9.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Recompress oversized image attachments and remove duplicated product images",
    "category": "Administration",
    "depends": ["base", "website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        "views/product_image_duplicate_view.xml",
        "wizard/product_image_dedup_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "license": "OPL-1",
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
