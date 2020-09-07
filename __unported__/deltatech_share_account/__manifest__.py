# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Share Account",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "description": """
Shared chart of account in multi-company

    """,

    "category": "Accounting",
    "depends": ["account"],

    "data": [
        'views/res_config_settings_views.xml',
        # 'views/account_invoice_views.xml'
    ],
    'application': False,
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
