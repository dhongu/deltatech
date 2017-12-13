# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
##############################################################################


{
    'name': 'Deltatech Expenses Deduction & Disposition of Cashing',
    'version': '10.0.1.0.0',
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

    ],

    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
