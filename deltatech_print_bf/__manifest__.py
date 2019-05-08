# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name" : "Print Invoice to ECR",
    "version" : "1.0",
    "author" : "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    'summary':'Generare fisier pentu casa de marcat',

    
    'category': 'Generic Modules',
    "depends" : ["account","web",'sale'],


 
    "license": "LGPL-3","data" : [ 'wizard/account_invoice_export_bf_view.xml',
               'wizard/sale_make_invoice_advance_views.xml',
               'data/data.xml'],
    "images": ['images/main_screenshot.png'],
    
    "active": False,
    "installable": True,
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

