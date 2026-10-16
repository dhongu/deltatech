{
    "images": ["static/description/main_screenshot.png"],
    "name": "POS Stock in Other Shops",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Show the stock of the other shops in the POS, on the product card and offline",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["deltatech_pos_stock"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "deltatech_pos_stock_shops/static/src/js/shop_stock_utils.esm.js",
            "deltatech_pos_stock_shops/static/src/js/shop_stock_popup.esm.js",
            "deltatech_pos_stock_shops/static/src/js/pos_store.esm.js",
            "deltatech_pos_stock_shops/static/src/js/product_card.esm.js",
            "deltatech_pos_stock_shops/static/src/xml/shop_stock_popup.xml",
            "deltatech_pos_stock_shops/static/src/xml/product_card.xml",
            "deltatech_pos_stock_shops/static/src/xml/product_screen.xml",
            "deltatech_pos_stock_shops/static/src/css/pos_stock_shops.css",
        ],
        "web.assets_unit_tests": [
            "deltatech_pos_stock_shops/static/tests/unit/**/*",
        ],
    },
    "installable": True,
    "license": "LGPL-3",
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
