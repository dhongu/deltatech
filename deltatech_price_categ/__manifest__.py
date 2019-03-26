# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Price List: Bronze Silver Gold Platinum",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Adaugare a 4 campuri in produs pentru 4 categorii de pret:
    1. pret bronz
    2. pret silver
    3. pret gold
    4. pret platinum
 
 

    """,

    "category": "Generic Modules/Stock",
    "depends": ["product", 'account'],

    "license": "AGPL-3",
    "data": [
        'views/product_view.xml',
    ],


    "installable": True,
}
