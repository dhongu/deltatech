# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Product Category per Company",
    "summary": "Products Category",
    "version": "19.0.1.0.2",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Sales",
    "depends": ["product", "base_setup"],
    "license": "OPL-1",
    "data": [
        "views/product_view.xml",
        "views/res_config_settings_views.xml",
        "security/product_security.xml",
    ],
    "images": ["images/main_screenshot.png"],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu"],
}
