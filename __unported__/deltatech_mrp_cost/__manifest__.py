# -*- coding: utf-8 -*-
# ©  2015-2017 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "MRP Cost",
    'version': '12.0.2.0.0',
    "author" : "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Manufacturing",
    "depends": [
        "mrp",
        "stock",
        "sale",
        "product",
        "deltatech_warehouse",
        'deltatech_purchase_price'

    ],
    "license": "LGPL-3",
    "data": [
        "views/mrp_view.xml",
        "data/mrp_data.xml",
        "views/mrp_production_templates.xml",
        "views/mrp_workcenter_view.xml"
    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
