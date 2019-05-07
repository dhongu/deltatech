# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Barcode Sale",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",

    'category': 'Sales',

    "depends": [
        "sale",
        'barcodes',
        'web_notify'
    ],


    "license": "LGPL-3",
    "data": [
        'views/sale_views.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,

}
