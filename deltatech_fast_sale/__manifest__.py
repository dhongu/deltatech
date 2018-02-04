# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Fast Sale",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
 
Features:

 - Buton in comanda de vanzare pentru a face pasii de confirmare, livrare si facturare
 


    """,
    "category": "Sales",
    "depends": ["base", "sale", 'stock','sale_stock'],

    "data": ['views/sale_view.xml',
             'views/stock_view.xml'],
    "active": False,
    "installable": True,
}
