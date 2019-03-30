# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Check Sale Price",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",

    'category': 'Sales',

    "depends": ["sale",'purchase'],

    "description": """
Features:    
 - Check sale price if is bigger that the highest purchase price
 
 - Vezi si modulul sale_margin 
 
""",
    "data": [
        'views/sale_views.xml'
    ],
    "active": False,
    "installable": True,

}
