# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name": "MRP Extension",
    "version": "2.0",
    "author": "Deltatech",
    "website": "",
    "description": """
    


    """,

    "category": "Generic Modules/Production",
    "depends": ["base", "mrp", "stock", "sale", "product"],

    "data": [
        "views/mrp_view.xml",
        #
        "report/deltatech_mrp_report.xml",

        "views/product_view.xml",

        'security/ir.model.access.csv'

    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
