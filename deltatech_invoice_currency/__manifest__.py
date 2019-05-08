# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Invoice Currency",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",

    "category": "Accounting",
    "depends": ["account", "l10n_ro_invoice_report", 'sale'],

    "license": "LGPL-3","data": ['views/account_invoice_view.xml',
             'views/report_invoice.xml'],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
}
