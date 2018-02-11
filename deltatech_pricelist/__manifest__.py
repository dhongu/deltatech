# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Price List Extension",
    'version': '10.0.1.0.0',
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:
    - pretul de lista din datele de baza ala produsului poate fa fie in alta moneda 

    """,

    'category': 'Sales',
    "depends": ["product"],

    "data": [
            'views/product_view.xml'
    ],

    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
