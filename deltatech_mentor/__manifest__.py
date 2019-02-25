# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "Deltatech Mentor Interface",
    "version": "2.0",
    "author": "Dorin Hongu",
    "website": "",
    "description": """

Functionalitati:
 - Permite exportul de date din Odoo pentru a fi importate in Mentor
   
Documentatia Mentor de import  din alte aplicatii:
 http://download.winmentor.ro/WinMentor/Documentatie/08_Structuri%20import%20din%20alte%20aplicatii/   
 ftp://ftp2.winmentor.ro/WinMentor/Documentatie/08_Structuri%20import%20din%20alte%20aplicatii/   
   
    - trebuie facuta mapare dintre categoriile de produse din Odoo si tipul contabil din mentor.   
    - conturile din Odoo sunt trimise in Mentor fara zeroruile de la sfarsit
    - daca este intalat modulul l10n_ro_stock_account se determina locatia din factura
        - din locatie de citeste codul
        - DepMP este codul utilizat in cazul in care nu este determinat un alt cod de locatie
   
    """,

    "category": "Accounting",
    "depends": [
        "date_range",
        "account",
        'product',
        'account_voucher',
        'deltatech_contact'
    ],

    'external_dependencies': {
        'python': ['configparser'],
    },
    "price": 200.00,
    "currency": "EUR",
    "license": "LGPL-3",
    "data": [
        'views/product_view.xml',
        'views/stock_location_view.xml',

        'wizard/export_mentor_view.xml',
        # 'wizard/import_mentor_view.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
