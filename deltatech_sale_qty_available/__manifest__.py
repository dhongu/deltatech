# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Sale Qty Available",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
 
Features:
 
 - Afisare campuri de cantitate disponibila in comanda de vanzare
 


    """,
    "category": "Warehouse",
    "depends": ["sale_stock"],

    "license":"LGPL-3","data": ['views/sale_view.xml','views/stock_picking_view.xml'],
    "active": False,
    "installable": True,
}
