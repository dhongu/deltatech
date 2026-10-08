# ©  2025 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "images": ["static/description/main_screenshot.png"],
    "name": "Image Optimizer",
    "version": "19.0.1.11.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "Recompress oversized image attachments, remove duplicated product images and product image backgrounds",
    "category": "Administration",
    "depends": ["base", "website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        "data/ir_actions_server.xml",
        "views/product_image_duplicate_view.xml",
        "wizard/product_image_dedup_view.xml",
        "wizard/image_background_wizard_view.xml",
    ],
    "assets": {
        "web.assets_backend": ["deltatech_image_optimize/static/src/scss/image_background_wizard.scss"],
    },
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "license": "OPL-1",
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
