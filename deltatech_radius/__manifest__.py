# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details
# Authors: João Figueira <jjnf@communities.pt>


{
    "name": "Deltatech RADIUS",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Generic Modules/Base",
    "depends": [ 'account'


    ],

    "license": "LGPL-3",
    "data": [
        'security/radius_security.xml',
        'security/ir.model.access.csv',
        'views/radius_view.xml',
        'views/res_partner_view.xml',
        'data/radius_data.xml',
        'wizard/radius_disconnect_view.xml'
    ],
    "images": ['images/main_screenshot.png'],

    "active": False,
    "installable": True,
}

