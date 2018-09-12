# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Print Invoice to ECR",
    "version": "1.0",
    "author": "Dorin Hongu",
    'summary': 'Generare fisier pentu casa de marcat',
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Generare fisier pentru program de tiparit Bon Fiscal din POS
   
    """,

    'category': 'Point Of Sale',
    "depends": ['point_of_sale'],

    "data": [
        'views/assets.xml',
        'views/account_journal_view.xml',
        'views/pos_config_view.xml'
    ],

    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
