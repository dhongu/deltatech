# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "MRP Record Production",
    'version': '11.0.2.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",

    "category": "Manufacturing",
    "depends": ['web','bus', 'mrp', 'hr_attendance','deltatech_mrp_group','deltatech_mrp_cost'],

    "license": "LGPL-3","data": [

        'views/mrp_record_view.xml',

        'views/mrp_workcenter_view.xml',
        'views/mrp_workorder_view.xml',
        'views/mrp_routing_view.xml',
        'views/mrp_production_templates.xml',
        'views/mrp_rework_view.xml',
        'wizard/start_production_view.xml',
        'wizard/mrp_record_view.xml',
        'wizard/mrp_mark_done_view.xml',
        'views/mrp_production_view.xml',
        'security/ir.model.access.csv',
        'views/web_asset_backend_template.xml',
        'data/data.xml',
    ],
    "images": ['images/main_screenshot.png'],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
