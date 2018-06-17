# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Claim 8D",
    "version": "1.0",
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Raportare 8D
  
  https://en.wikipedia.org/wiki/Eight_Disciplines_Problem_Solving
  
   
    """,

    'category': 'Sales Management',
    "depends": [
        'deltatech', 'product',
        'deltatech_simple_crm_claim'
        # "crm_claim"
    ],

    "data": [
        'security/ir.model.access.csv',
        'views/report8d.xml',
        'views/crm_claim_view.xml'
    ],

    "active": False,
    "installable": True,
}
