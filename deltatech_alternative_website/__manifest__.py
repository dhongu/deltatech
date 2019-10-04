# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Website alternative code",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "description": """

Functionalitati:
    - cautare produs dupa cod echivalent
    - afisare imagini produse in magazinul virtual cu watermark

    """,

    "category": "Website",
    "depends": ["website_sale", "deltatech_alternative"],

    'data': [
        'views/product_view.xml',
        'views/templates.xml'
    ],

    "installable": True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
