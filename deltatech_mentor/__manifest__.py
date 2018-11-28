# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Mentor Interface",
    "version": "2.0",
    "author": "Dorin Hongu",
    "website": "",
    "description": """

Functionalitati:
 - Permite exportul de date din Odoo pentru a fi importate in Mentor
   
Documentatia Mentor de import  din alte aplicatii:
 http://download.winmentor.ro/WinMentor/Documentatie/08_Structuri%20import%20din%20alte%20aplicatii/   
 ftp://ftp2.winmentor.ro/WinMentor/Documentatie/08_Structuri%20import%20din%20alte%20aplicatii/   
   
    """,

    "category": "Generic Modules/Base",
    "depends": ["date_range", "account", 'product','account_voucher'],

    'external_dependencies': {
        'python': ['configparser'],
    },

    "data": [
        'views/product_view.xml',

        'wizard/export_mentor_view.xml',
        #'wizard/import_mentor_view.xml'
    ],

    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
