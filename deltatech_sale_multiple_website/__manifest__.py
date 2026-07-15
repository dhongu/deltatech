{
    "images": ["static/description/main_screenshot.png"],
    "name": "eCommerce Qty Multiple",
    "summary": "Enforce product quantity multiples in eCommerce",
    "version": "19.0.1.1.0",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "license": "LGPL-3",
    "depends": ["deltatech_sale_multiple", "website_sale_stock"],
    "data": [
        "views/templates.xml",
        "views/product_view.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deltatech_sale_multiple_website/static/src/js/qty_popover.esm.js",
        ],
    },
    "development_status": "Beta",
    "maintainers": ["dhongu"],
}
