# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Barcode Picking",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",

    'category': 'Warehouse',

    "depends": [
        "stock",
        'barcodes',
        'web_notify'
    ]
    ,

    "description": """
Features:    
 - Adds products to picking using barcode scanner
 
""",
    "price": 15.00,
    "currency": "EUR",
    "license": "LGPL-3",
    "data": [
        'views/picking_views.xml',
        'views/stock_inventory_view.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,

}
