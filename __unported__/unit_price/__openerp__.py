# -*- coding: utf-8 -*-
{
    'name': "terra_unitprice",

    'summary': """
        Displays unit price in stock""",

    'description': """
        Displays unit price in stock
    """,

    'author': "Terrabit",
    'website': "http://www.terrabit.ro",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
