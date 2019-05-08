# -*- coding: utf-8 -*-
# ©  2018 Terrabit
# See README.rst file on addons root folder for license details

{
    "name": "List Extension",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


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


