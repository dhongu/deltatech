# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "MRP Bom",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:
----------------
 - adaugare nume la fiecare componenta din ldm
 - adugare buton pentru accesare rapida sub-LDM

    """,

    "category": "Manufacturing",
    "depends": ['mrp'],

    "license": "LGPL-3",
    "data": [
        'views/mrp_bom_view.xml'
             ],
    'qweb': [

    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
