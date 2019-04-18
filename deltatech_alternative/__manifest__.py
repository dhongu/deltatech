# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Products Alternative",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "category": "Generic Modules/Inventory Control",
    "depends": ["product", 'stock'],

    "description": """
Features:    
 - New model: product_catelog
 - A module that add alternative on the product form
 - Camp nou in produs (used for) pentru a indica la ce poate fi folosit produsul
 
 
""",
    "data": [
        "views/product_view.xml",
        'security/ir.model.access.csv',
    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
