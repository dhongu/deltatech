# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Claim 8D",
    "version": "1.1",
    "author" : "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    'category': 'Sales Management',
    "depends": [
         'product',
        'deltatech_simple_crm_claim'
        # "crm_claim"
    ],

    "license": "LGPL-3",
    "data": [
        'security/ir.model.access.csv',
        'views/report8d.xml',
        'views/crm_claim_view.xml'
    ],
    "images": ['images/main_screenshot.png'],

    "active": False,
    "installable": True,
}
