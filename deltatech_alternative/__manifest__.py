# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Products Alternative",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    'summary': 'Alternative product codes',
    "category": "Sales",
    "depends": ["product", 'stock'],


    "license": "LGPL-3",
    "data": [
        "views/product_view.xml",
        'security/ir.model.access.csv',
    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
