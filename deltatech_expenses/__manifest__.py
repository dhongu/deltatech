# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


{
    'name': 'Deltatech Expenses Deduction & Disposition of Cashing',
    'version': '12.0.1.0.0',
    "category": 'Accounting & Finance',
    'complexity': "easy",
    'description': """

Expenses Deduction & Disposition of Cashing
-------------------------------------------

- Introducerea decontului de cheltuieli intr-un document distict ce genereaza automat chitante de achizitie
- Validarea documentrului duce la generarea notelor contabile de avans si inegistrarea platilor

Este necesar sa fie definit un jurnal nou pentru decontul de cheltuieli la care se aloca contul 542

- 
		
    """,
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    'images': [''],
    'depends': [
        'account',
        'account_voucher',
        'product',
        # 'l10n_ro', # este chiar necesar ?
        # 'l10n_ro_account_voucher_cash' # este chiar necesar ?
    ],
    'data': [
        #'views/account_voucher_view.xml',
        'views/deltatech_expenses_deduction_view.xml',
        #'views/deltatech_expenses_deduction_report.xml',
        #'wizard/expenses_deduction_from_account_voucher_view.xml',
        #"data/product_data.xml",
        "data/partner_data.xml",
        #'views/report_expenses.xml',
        'security/ir.model.access.csv'

    ],
    "images": ['images/main_screenshot.png'],
    'installable': True,

}


