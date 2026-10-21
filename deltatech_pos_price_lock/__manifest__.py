{
    "images": ["static/description/main_screenshot.png"],
    "name": "POS Price Lock",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Block price changes in the POS for every cashier, managers included",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["point_of_sale"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "deltatech_pos_price_lock/static/src/js/pos_store.esm.js",
        ],
        "web.assets_unit_tests": ["deltatech_pos_price_lock/static/tests/unit/**/*"],
    },
    "installable": True,
    "license": "LGPL-3",
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
