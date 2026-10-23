{
    "images": ["static/description/main_screenshot.png"],
    "name": "POS Cashier Close Register",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Cashiers close their own register, without the other manager rights",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "support": "support@terrabit.ro",
    "depends": ["pos_hr"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "deltatech_pos_cashier_close/static/src/js/*.esm.js",
        ],
        "web.assets_unit_tests": ["deltatech_pos_cashier_close/static/tests/unit/**/*"],
    },
    "installable": True,
    "license": "OPL-1",
    "price": 10.00,
    "currency": "EUR",
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
