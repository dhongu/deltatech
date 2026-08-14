{
    "images": ["static/description/main_screenshot.png"],
    "name": "Deltatech POS Stock",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Display stock in POS",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["point_of_sale", "stock"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "deltatech_pos_stock/static/src/xml/product_card.xml",
            "deltatech_pos_stock/static/src/js/product_card.esm.js",
            "deltatech_pos_stock/static/src/css/pos_stock.css",
        ],
    },
    "installable": True,
    "license": "LGPL-3",
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
