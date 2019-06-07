# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Products Category",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",

    'category': 'Sales',

    "depends": ["product"],


    "license": "LGPL-3",
    "data": [
        "views/product_view.xml",
        'views/res_config_settings_views.xml',
        'security/product_security.xml'
    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
