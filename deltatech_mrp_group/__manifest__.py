# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "MRP Group Production Order",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",

    "category": "Manufacturing",
    "depends": ["mrp","sale_stock","purchase",'sale_management'],

    "license": "LGPL-3","data": [
        "views/mrp_production_view.xml",
        "views/sale_view.xml",
       # "views/procurement_views.xml",
        "wizard/mrp_order_group_view.xml",
        "wizard/sale_order_group_view.xml",
        "wizard/mrp_workorder_group_view.xml",
        "data/data.xml"
    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
