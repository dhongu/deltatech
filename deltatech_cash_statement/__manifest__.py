# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Cash Statement Extension",
    'version': '12.0.3.0.0',
    "author": "Dorin Hongu",
    "website": "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting & Finance',
    "depends": ["account"],

    "data": [
        'wizard/account_cash_update_balances_view.xml'
    ],

    "images": ['images/main_screenshot.png'],
    "installable": True,
}
