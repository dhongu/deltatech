# -*- coding: utf-8 -*-
# ©  2015-2017 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "MRP Warehouse",
    "version": "1.0",
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:


    """,

    "category": "Warehouse",
    "depends": [
         "stock","product","procurement"
    ],

    "license":"LGPL-3","data": [
        'views/company_view.xml',
        'views/stock_warehouse_view.xml',
    ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
