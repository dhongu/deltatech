# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Stock Date",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
- preluare data efectiva din trecut in documente 
 
    """,

    "category": "Warehouse",
    "depends": ["base", "stock"],

    "data": ['wizard/stock_immediate_transfer_view.xml'

             ],
    'application': False,
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
