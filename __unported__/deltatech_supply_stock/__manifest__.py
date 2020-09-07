# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Supply Stock",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "description": """

Functionalitati:

    - generare comenzi de aprovizionare pentru produsele la care Estimatul este negativ.

    """,

    "category": "Warehouse",
    "depends": ['sale_stock', 'mrp', 'deltatech_warehouse'],

    "data": [
        # 'wizard/procurement_compute_wizard_view.xml',
        'wizard/procurement_compute_products_view.xml',
        'wizard/mrp_check_availability_view.xml',

    ],

    "active": False,
    "installable": True,
}
