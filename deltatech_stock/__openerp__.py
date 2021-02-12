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
    "name" : "Deltatech Stock",
    "version" : "1.0",
    "author" : "Deltatech",
    "website" : "",
    "description": """
    
Ajustari:
    
   
   
product.category 
    - adaugat camp sequence_id folosit pt generarea de coduri la produse 
    
product.product 
    - modificat metoda create - generare de cod in functie de categorie daca la referinta se trece auto
    
   

    
stock.move 
    - adaugat campul amount - cu valoarea miscari
    - modificat metoda  create pt a completa campul amount

    

    
stock_inventory 
    - modificat metoda  action_confirm pt a genera miscarile de stoc la data din inventar nu la cea curenta
    



    """,
    
    "category" : "Generic Modules/Production",
    "depends" : ["base","stock","product","deltatech_contact"],


    "data" : [      
 
                 "stock_view.xml",
                
                "product_view.xml",
                "product_sequence_data.xml",
                "wizard/stock_transfer_view.xml",
 
              #  'security/ir.model.access.csv'
                
                ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

