# -*- coding: utf-8 -*-
# ©  2008-2020 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "Maintenance Extension",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "",


    'category': 'Human Resources',
    "depends": ["maintenance",'stock'],

    "data": [
        'security/ir.model.access.csv',
        'views/maintenance_view.xml',
        'views/stock_picking_view.xml',
        #'views/res_config_view.xml',
    ],
    "images": ['static/description/main_screenshot.png'],
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
