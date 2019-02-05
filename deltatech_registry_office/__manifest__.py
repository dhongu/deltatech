# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Registry Office",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",

    'category': 'Document Management',

    "depends": ['document', 'mail', 'deltatech_contact'],

    "description": """
Features:    
 - 
 
""",
    "data": [
        'wizard/solution_view.xml',
        'wizard/user_view.xml',
        'views/registry_office_view.xml',
        'data/data.xml',
        'security/ir.model.access.csv'
    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
    'application': True,
}

