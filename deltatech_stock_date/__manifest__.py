# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Stock Date",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    
    "description":
                """
                    The picking effective date can be changed when the picking is validated.
                    All the stock moves will have the picking's effective date.
                """,


    "category": "Warehouse",
    "depends": ["base", "stock"],

    "license": "LGPL-3","data": ['wizard/stock_immediate_transfer_view.xml'

             ],
    "images": ['images/main_screenshot.png'],
    'application': False,
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
