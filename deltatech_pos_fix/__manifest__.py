{
    "name": "Deltatech POS Fix",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Fix POS total calculation when using tax-included fiscal position mapping",
    "license": "LGPL-3",
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": ["point_of_sale"],
    "data": [],
    "assets": {
        "point_of_sale._assets_pos": ["deltatech_pos_fix/static/src/app/models/pos_order_line.esm.js"],
    },
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
}
