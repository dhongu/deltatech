# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Contacts",
    'version': '12.0.1.3.0',
    "author": "Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Adaugare campuri suplimentare in datele de contact: birthdate, CNP,  nr carte de identitate

   
    """,

    "category": "Generic Modules/Base",
    "depends": ["base"],

    "data": [
        'views/res_partner_view.xml',
        #'security/partner_security.xml',
        #'security/ir.model.access.csv'
    ],

    "images": ['images/main_screenshot.png'],
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
