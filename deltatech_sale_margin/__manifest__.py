# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Sale Margin",
    'version': '12.0.1.0.0',
    "category": "Sales Management",
    "author": "Dorin Hongu",
    "website": "",
    "description": """
 
Features:
 - New technical access group for display margin and purchase price in sale order and customer invoice
 - New technical access group to prevent changing price in sale order (and customer invoice) 
 - New technical access group to allow sale price  below the purchase price
 - Warning/Error on sale order if sale price is below the purchase price
 - Warning/Error on customer invoice if sale price is below the purchase price
 - New report for analysis profitability
 - Calcul comisione de vanzari
 - Pretul de vanzare este fara TVA calculat prin modulul l10n_ro_invoice_report

    """,

    "depends": [
        "sale_margin",
        'account',
        #'l10n_ro_invoice_report'
    ],

    "license": "LGPL-3",
    "data": [
        'security/sale_security.xml',
        'security/ir.model.access.csv',
        'views/sale_margin_view.xml',
        'views/account_invoice_view.xml',
        'report/sale_margin_report.xml',
        'views/commission_users_view.xml',
        'wizard/commission_compute_view.xml',
        'wizard/update_purchase_price_view.xml'
    ],
    "images": ['static/description/main_screenshot.png'],
    "active": False,
    "installable": True,
}
