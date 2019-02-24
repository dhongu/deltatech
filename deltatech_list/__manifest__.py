# -*- coding: utf-8 -*-
# ©  2018 Terrabit
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech List",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
 
 Features:
 - Keep selection after sorting
 - Display a legend button in the list view.  The legend is extracted from the action-help field if it defines a tag with id "legend".
 
 
    """,

    "category": "Generic Modules",
    "depends": ['web'],

    "license": "LGPL-3",
    "data": [

        'views/assets.xml',

    ],
    'qweb': [
        "static/src/xml/*.xml",

    ],
    "images": ['images/main_screenshot.png'],

    "installable": True,
    'application': True,
}


