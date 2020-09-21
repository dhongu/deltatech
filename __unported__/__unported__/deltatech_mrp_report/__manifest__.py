# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
##############################################################################

{
    "name" : "Deltatech Manufacturing Resource Planning",
    "version" : "3.0",
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


    "license": "LGPL-3","data" : [      
                #"views/mrp_view.xml",
                "views/mrp_report.xml",
                "report/deltatech_mrp_report.xml", 

                "views/product_view.xml",
                'views/order_report.xml',
                'security/ir.model.access.csv'
                
                ],
    "active": False,
    "installable": True,
}
