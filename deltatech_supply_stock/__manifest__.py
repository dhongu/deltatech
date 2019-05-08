# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Supply Stock",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Warehouse",
    "depends": ['sale_stock', 'mrp', 'deltatech_warehouse'],

    "license": "LGPL-3","data": [
        #'wizard/procurement_compute_wizard_view.xml',
        'wizard/procurement_compute_products_view.xml',
        'wizard/mrp_check_availability_view.xml',

    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
}


