# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Payment to Statement",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Adugare platilor in extrasele de banca
 
 This module added features on customer/supplier payments to allow account user to link
 payment with bank statement direct through payment menu or customer/supplier invoices register payment option. 
 After selecting and validating payment, module will add bank statement line on selected bank statement.
   
    """,

    "category": "Accounting",
    "depends": [
        "account",
    ],

    "data": [
        'views/account_payment_view.xml',
        'views/account_view.xml',
        'views/account_journal_dashboard_view.xml'

    ],

    "active": False,
    "installable": True,
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
