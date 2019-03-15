# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Barcode Purchase ",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",

    'category': 'Purchases',

    "depends": ["purchase",'barcodes'],

    "description": """
Features:    
 - Add product to the purchase order using barcode scanner
 
""",
    "data": [
        'views/purchase_views.xml'
    ],
    "active": False,
    "installable": True,

}
