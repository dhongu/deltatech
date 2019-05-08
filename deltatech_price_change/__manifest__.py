# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Price Change",
    "version": "1.0",
    "author": "Deltatech",
    "website": "",


    "category": "Generic Modules",
    "depends": ["base", "stock", "product", "sale"],

    "license": "LGPL-3","data": [
         "views/product_view.xml",

        "views/product_price_change_view.xml",
        # "views/purchase_report.xml",
        "views/price_change_report.xml",
        "views/report_pricechange.xml",

        'security/ir.model.access.csv'
    ],
    "images": ['images/main_screenshot.png'],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
