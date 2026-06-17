# ©  2024 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "POS Add Extra Line",
    "summary": "POS Add Extra Line",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "depends": [
        "point_of_sale",
        "deltatech_sale_add_extra_line",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "deltatech_sale_add_extra_line_pos/static/src/js/models.esm.js",
        ],
    },
    "license": "OPL-1",
    "data": [],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Production/Stable",
    "maintainers": ["dhongu"],
}
