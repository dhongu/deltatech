# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Invoice Currency",
    'version': '11.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
----------------

 - Calcul pret produs in functie de lista de preturi aferenta clientului/furnizorului


    """,
    "category": "Accounting",
    "depends": ["account", "l10n_ro_invoice_report", 'sale'],

    "data": ['views/account_invoice_view.xml',
             'views/report_invoice.xml'],
    "active": False,
    "installable": True,
}
