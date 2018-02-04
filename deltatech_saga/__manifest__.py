# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech SAGA Interface",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Permite exportul de date din Odoo pentru a fi importate in SAGA
 - Permite importul de clienti si furnizori din SAGA
 - Partenerii au doua referinte pentru codurile de client respectiv de furnizor din SAGA
 - Categoriile de produse au un camp nou pentru tipul de articol din SAGA  
  
   
    """,

    "category": "Accounting",
    "depends": [
        "base",
        "account",
    ],

    "data": [
        'data/data.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml',
        'wizard/export_saga_view.xml',
        'wizard/import_saga_view.xml',
    ],

    "active": False,
    "installable": True,
}


