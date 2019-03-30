# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Price List Extension",
    'version': '10.0.1.0.0',
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:
    - pretul de lista din datele de baza ala produsului poate sa fie in alta moneda 

    """,

    'category': 'Sales',
    "depends": ['base',"product"],

    "data": [
        #'views/product_view.xml',
        'views/res_company_view.xml'
    ],
    "images": ['static/description/main_screenshot.png'],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
