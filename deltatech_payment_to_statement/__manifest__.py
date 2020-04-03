# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Payment to Statement",
    'version': '13.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Accounting",
    "depends": [
        "account",
    ],
    "license": "LGPL-3",
    "data": [
        'views/account_payment_view.xml',
        'views/account_view.xml',
        'views/account_journal_dashboard_view.xml'

    ],

    "images": ['images/main_screenshot.png'],
    "installable": True,
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
