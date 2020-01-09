# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


{
    'name': 'Expenses Deduction & Disposition of Cashing',
    'version': '12.0.1.0.0',
    "category": 'Accounting & Finance',
    'complexity': "easy",

    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    'images': [''],
    'depends': [
        'account',
        'account_voucher',
        'product',
        'deltatech_partner_generic'
        # 'l10n_ro', # este chiar necesar ?
        # 'l10n_ro_account_voucher_cash' # este chiar necesar ?
    ],
    "license": "LGPL-3",
    'data': [
        #'views/account_voucher_view.xml',
        'views/deltatech_expenses_deduction_view.xml',

        'views/deltatech_expenses_deduction_report.xml',
        'views/report_expenses.xml',
        #'wizard/expenses_deduction_from_account_voucher_view.xml',
        #"data/product_data.xml",
        "data/partner_data.xml",
        #'views/report_expenses.xml',
        'security/ir.model.access.csv'

    ],
    "images": ['images/main_screenshot.png'],
    'installable': True,

}


