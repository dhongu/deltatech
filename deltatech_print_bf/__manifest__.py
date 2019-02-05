# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

{
    "name" : "Deltatech Print Invoice to ECR",
    "version" : "1.0",
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    'summary':'Generare fisier pentu casa de marcat',
    "description": """

Functionalitati:
 - Generare fisier pentru program de tiparit Bon Fiscal
 - definire client generic pentru care se fac in mod automat Bonuri fiscale

De pregatit:
 - Trebuie definit un jurnal de vanzari pentru Bonru Fiscale cu codul BF
   
    """,
    
    'category': 'Generic Modules',
    "depends" : ["account","web",'sale'],


 
    "data" : [ 'wizard/account_invoice_export_bf_view.xml',
               'wizard/sale_make_invoice_advance_views.xml',
               'data/data.xml'],
    "images": ['images/main_screenshot.png'],
    
    "active": False,
    "installable": True,
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

