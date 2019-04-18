# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


{
    "name": "Deltatech Price Change",
    "version": "1.0",
    "author": "Deltatech",
    "website": "",
    "description": """
 
Scopul modulului este de a controla modificarile de pret la produse.
La fiecare modificare de pret intocmeste un document care este datat si numerotat.



Nota
    * campul list_price - este editabil in template si este editbil si sta la baza determinarii pretului
    * campul lst_price  - este pretul calculat si apare la variantele de produs


   

    """,

    "category": "Generic Modules",
    "depends": ["base", "stock", "product", "sale"],

    "data": [
         "views/product_view.xml",

        "views/product_price_change_view.xml",
        # "views/purchase_report.xml",
        "views/price_change_report.xml",
        "views/report_pricechange.xml",

        'security/ir.model.access.csv'
    ],
    "images": ['images/main_screenshot.png'],
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
