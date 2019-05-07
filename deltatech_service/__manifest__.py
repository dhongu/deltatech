# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Services",
    'version': '12.0.2.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Service Management",
    "depends": [
        "base",
        "product",
        "account",
        "date_range"
    ],

    "license": "LGPL-3",
    "data": [
        'data/data.xml',
        'security/service_security.xml',
        'security/ir.model.access.csv',
        "views/service_consumption_view.xml",
        "views/service_agreement_view.xml",

        "wizard/service_billing_preparation_view.xml",
        "wizard/service_billing_view.xml",
        "wizard/service_distribution_view.xml",
        "wizard/service_price_change_view.xml",
        "wizard/service_change_invoice_date_view.xml",
        # "views/account_invoice_penalty_view.xml",


    ],
    "images": ['images/main_screenshot.png'],
    'application': True,
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
