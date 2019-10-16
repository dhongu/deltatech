# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details
{
    "name": "MRP Process Manufacturing",
    'version': '12.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Manufacturing",
    "depends": [
        "mrp",'deltatech_mrp_param'
    ]
    ,

    "license": "LGPL-3",
    "data": [
        'wizard/cleaning_view.xml',
        'views/mrp_workorder_view.xml',
        'views/mrp_routing_views.xml',
        'views/mrp_workcenter_view.xml',
        'report/mrp_production_templates.xml',
        'report/mrp_report_views_main.xml',

    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,
}
