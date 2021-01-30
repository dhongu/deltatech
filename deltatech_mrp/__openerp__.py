# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details

{
    "name" : "Deltatech Manufacturing Resource Planning",
    "version" : "2.0",
    "author" : "Deltatech",
    "website" : "",
    "description": """
    
Ajustari:
    
mrp.bom 
     
    - adaugat campul value_overhead - procent pt cheltuieli indirecte
    - rotunjire cantitate la explozia BOM in conformitate cu definitia unitati de masura
    
mrp.production
   
    - modificat metoda action_confirm 
        - modificare date_expected pentru miscarile generate de comanda de productie
        - generarea automata a unui lot de productie daca produsul este gestionat in loturi
             
mrp.production.product.line 
    - adaugat camp cantitate disponibila
    - adaugat metoda onchange_product_id    
   
 
  
Rapoarte:

deltatech.mrp.report 
    - raport pt analiza costuri de productie

report.mrp.production.order.deltatech 
    - formular pentru comanda de productie


    """,
    
    "category" : "Generic Modules/Production",
    "depends" : ["base","mrp","stock","sale","product"],


    "data" : [      
                "views/mrp_view.xml",
                "views/mrp_report.xml",
                "report/deltatech_mrp_report.xml", 

                "views/product_view.xml",
                'views/order_report.xml',
                'security/ir.model.access.csv'
                
                ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

