# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Mentor Interface",
    'version': '11.0.2.0.1',
    "author": "Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "support": "odoo@terrabit.ro",

    "category": "Accounting",
    "depends": [
        "date_range",
        "account",
        'product',
        'account_voucher',
        'deltatech_contact'
    ],

    'external_dependencies': {
        'python': ['configparser'],
    },
    "price": 200.00,
    "currency": "EUR",
    "license": "LGPL-3",
    "data": [
        'views/product_view.xml',
        'views/stock_location_view.xml',

        'wizard/export_mentor_view.xml',
        # 'wizard/import_mentor_view.xml'
    ],
    "images": ['images/main_screenshot.png'],

    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
