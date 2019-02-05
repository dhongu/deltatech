# -*- coding: utf-8 -*-
# ©  2015-2017 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "MRP Warehouse",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - definire  camp scrap (pierderi)
 - definire furnizor implicit
 - definire depozit implicit
 
    """,

    "category": "Warehouse",
    "depends": [
        "stock", "product"
    ],

    "data": [
        'views/company_view.xml',
        'views/stock_warehouse_view.xml',
        'views/template_product_view.xml',
        'data/data.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
