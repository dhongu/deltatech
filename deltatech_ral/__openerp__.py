# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech RAL",
    "version": "1.0",
    "author": "Dorin Hongu",
    "website": "",
    "description": """
Permite selectarea unui pigment (RAL) in comanda de productie
Pigmentul este un material care are codul ce incepe cu RAL 
Daca in BOM este folosit pigmentul RAL 0000 acesta va fi inlocuit cu pigmentul  din comanda de productie.
Lotul se va crea in mod automat la confirmarea comenzi si va avea pigmentul din comanda de productie

    """,
    "category": "Generic Modules/Other",
    "depends": ["base", "stock", "mrp"],

    "data": [
        "views/stock_view.xml",
        "views/mrp_view.xml"
    ],

    "installable": True,
}
