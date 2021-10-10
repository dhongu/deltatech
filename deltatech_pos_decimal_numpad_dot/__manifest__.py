# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech POS - Numpad Dot as decimal separator",
    "summary": "Numpad Dot as decimal separator",
    "version": "15.0.1.0.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "category": "Sales/Point of Sale",
    "depends": ["point_of_sale"],
    "license": "LGPL-3",
    "data": [
        # "views/assets.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "development_status": "Beta",
    "maintainers": ["dhongu"],
    "assets": {"point_of_sale.assets": ["/deltatech_pos_decimal_numpad_dot/static/src/js/NumberBuffer.js"]},
}
