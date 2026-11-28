{
    "images": ["static/description/main_screenshot.png"],
    "name": "POS Price Lock",
    "version": "20.0.1.1.1",
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
            "deltatech_pos_price_lock/static/src/js/access_right_plugin.esm.js",
        ],
        "web.assets_unit_tests": ["deltatech_pos_price_lock/static/tests/unit/**/*"],
    },
    "installable": True,
    "license": "OPL-1",
    "price": 10.00,
    "currency": "EUR",
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
