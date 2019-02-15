# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Consignment",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",

    'category': 'Sales',

    "depends": ["sale",'stock','purchase'],

    "description": """
Features:    
 - Generare factura de achizitie dupa vanzarea produselor
 
""",
    "license":"LGPL-3","data": [
        'views/purchase_view.xml'
    ],
    "active": False,
    "installable": True,

}
