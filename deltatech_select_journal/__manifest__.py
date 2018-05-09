# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Select Journal",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    'summary': 'Selectie jurnal',
    "description": """

Functionalitati:
 - Selectie jurnal in momentul generarii facturii din comanda de vanzare
 -  
   
    """,

    'category': 'Sales',
    "depends": ['sale'],

    "data": [
        'wizard/sale_make_invoice_advance_views.xml',
    ],

    "active": False,
    "installable": True,
}
