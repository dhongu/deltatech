# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Stock Transfer",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 
 - Wizard pt transfer produse dintr-o locatie in alta
 

    """,

    "category": "Stock",
    "depends": [
        "stock"
    ]
    ,

    "license": "LGPL-3",

    "data": [
        'wizard/stock_transfer_view.xml',
        'views/stock_view.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
}
