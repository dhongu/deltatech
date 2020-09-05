# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Average Payment Period",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    'category': 'Accounting & Finance',
    "depends": ['account'],

    "license": "AGPL-3",

    "data": [
        'views/account_view.xml',
        'report/account_average_payment_view.xml',
        'security/ir.model.access.csv'
    ],

    "images": ['images/main_screenshot.png'],
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
