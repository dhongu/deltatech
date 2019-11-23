# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details



{
    'name': "Product Catalog",
    'version': '12.0.1.0.0',
    'summary': """This module helps to print the catalog of the multi products""",

    'category': 'Inventory',
    "author": "Terrabit, Dorin Hongu",
    'company': 'Terrabit',
    'maintainer': 'Terrabit',
    'website': "https://www.terrabit.ro",
    'depends': ['base', 'stock', 'website_sale'],
    'data': [

        'report/product_catalog_report.xml',
        'report/product_catalog_template.xml',
    ],
    "images": ['images/main_screenshot.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
