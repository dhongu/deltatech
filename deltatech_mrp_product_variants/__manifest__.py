# -*- coding: utf-8 -*-
# ©  2015-2017 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "MRP Product Variants",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:
 - Șablon de produs în comanda de producție


    """,

    "category": "Manufacturing",
    "depends": [
        "mrp",

    ],

    "license": "LGPL-3","data": [
        "views/mrp_view.xml",
        'views/mrp_product_produce_views.xml',
        "views/mrp_production_templates.xml",
        "views/product_view.xml"

    ],
    "images": ['images/main_screenshot.png'],

    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
