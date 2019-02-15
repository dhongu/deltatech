# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Stock Date",
    'version': '10.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
- preluare data efectiva din trecut in documente 
 
    """,

    "category": "Generic Modules/Other",
    "depends": ["base", "stock", "deltatech"],

    "license":"LGPL-3","data": [
        'wizard/stock_immediate_transfer_view.xml',
        'wizard/stock_backorder_confirmation_view.xml'
             ],
    'application': False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
