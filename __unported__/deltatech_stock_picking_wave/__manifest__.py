# -*- coding: utf-8 -*-

{
    "name": "Stock Picking Wave Extension",
    'version': '10.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "description": """
    
Functionalitati:
----------------
    - afisare masa si volum la fiecare livrare
    - afisare in picking_wave a produselor din livrari

    """,

    "category": "Generic Modules/Stock",
    "depends": ['stock_picking_wave', 'delivery', 'stock'],

    "data": [
        'views/stock_picking_wave_view.xml'
    ],

    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
