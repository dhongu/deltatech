{
    "images": ["static/description/main_screenshot.png"],
    "name": "POS Stock Operations",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Receipts and deliveries from the POS session, by piece or by pack",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["point_of_sale", "stock", "purchase_stock", "deltatech_pos_stock"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/pos_stock_operation_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "deltatech_pos_stock_ops/static/src/xml/stock_ops_dialog.xml",
            "deltatech_pos_stock_ops/static/src/xml/navbar.xml",
            "deltatech_pos_stock_ops/static/src/js/stock_ops_dialog.esm.js",
            "deltatech_pos_stock_ops/static/src/js/navbar.esm.js",
        ],
    },
    "installable": True,
    "license": "LGPL-3",
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
