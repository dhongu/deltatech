# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "MRP Report",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Manufacturing",
    "depends": [
        "stock",
        "date_range"

    ]
    ,

    "license": "LGPL-3","data": [
        'views/product_view.xml',
        'wizard/mrp_summary_view.xml',
        'views/mrp_summary_template.xml'
    ],
    "images": ['images/main_screenshot.png'],

    "active": False,
    "installable": True,
}
