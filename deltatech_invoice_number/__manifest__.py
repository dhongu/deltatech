# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Invoice Number",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",

    "category": "Accounting",
    "depends": ["account_invoicing"],

    "license": "LGPL-3",

    "data": [
        'security/sale_security.xml',
        'views/account_invoice_view.xml',
        'wizard/account_invoice_change_number_view.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,
}
