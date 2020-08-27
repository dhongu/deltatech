# -*- coding: utf-8 -*-
# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
{
    'name': 'Delivery and Payment',
    'category': 'Website',
    'summary': 'eCommerce Delivery and Payment constrains',

    'version': '1.0',

    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",

    'depends': ['website_sale'],
    'data': [
        'views/delivery_view.xml',
        'views/assets.xml'
    ],

    "images": ['static/description/main_screenshot.png'],
    "installable": True,

}
