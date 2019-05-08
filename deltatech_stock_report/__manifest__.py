# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name": "Deltatech Stock Reports",
    "version": "1.0",
    "author" : "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Generic Modules",
    "depends": ["base", "stock","stock_account" ],


    "license": "LGPL-3",
    "data": [ 'security/ir.model.access.csv',
              "report/stock_picking_report.xml"],
    "images": ['images/main_screenshot.png'],
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
