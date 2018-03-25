# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    'name': 'Widget Google Maps',
    'version': '11.0.2.1.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    'license': 'AGPL-3',
    'category': 'Odoo  widgets',
    'depends': ['web'],
    'data': ['views/web_gmaps_assets.xml'],

    'qweb': [
        'static/src/xml/resource.xml'
    ],
    'installable': True,
    'application': False,
    'bootstrap': True,
    'auto_install': False,
}
