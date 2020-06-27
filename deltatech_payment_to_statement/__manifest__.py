# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Payment to Statement",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "summary": "And payment to statement",

    "category": "Accounting",
    "depends": [
        "account",
        "payment"
    ],
    "license": "LGPL-3",
    "data": [
        'views/account_payment_view.xml',
        'views/account_view.xml',
        'views/account_journal_dashboard_view.xml'

    ],

    "images": ['static/description/main_screenshot.png'],
    "installable": True,
    'post_init_hook': '_set_auto_auto_statement',
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
