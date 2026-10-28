{
    "images": ["static/description/main_screenshot.png"],
    "name": "POS Price Sync",
    "version": "20.0.1.0.2",
    "category": "Point of Sale",
    "summary": "Push live product price changes to already open POS sessions",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["point_of_sale"],
    "data": [],
    "assets": {
        "point_of_sale._assets_pos": [
            "deltatech_pos_price_sync/static/src/js/pos_price_synchronisation.esm.js",
        ],
    },
    "installable": True,
    "license": "LGPL-3",
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
