# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Cash Statement Extension",
    'version': '10.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - actualizare automata sold la casa
   
    """,

    'category': 'Accounting',
    "depends": ["account"],

    "license":"LGPL-3","data": [
        'wizard/account_cash_update_balances_view.xml'
    ],

    "active": False,
    "installable": True,
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
