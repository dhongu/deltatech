# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Fast Purchase",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    'summary': 'Achizitie rapida',

    "description": """
 
Features:
---------
 - Buton in comanda de aprovizionare pentru a face pasii de confirmare, receptie si facturare
 - Buton in repetie pentru a introduce direct factura
 - Buton in camoanda de aprovizonare pentru generare de receptie in baza unui aviz


    """,
    "category": "Generic Modules/Stock",
    "depends": [
        "base",
        "purchase_stock",
        "stock"
    ],

    "license": "LGPL-3",
    "data": [
        'views/purchase_view.xml',
             'views/stock_view.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
}
