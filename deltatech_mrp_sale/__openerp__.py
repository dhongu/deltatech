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
    "name" : "Deltatech MRP Sale",
    "version" : "2.0",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """
    
Functionalitati:
 - Se permite intocmirea unei liste de produse in comanda de vanzare
 - In lista de produse se pot defini atribute
 - se face explozia listie initiale in a lista de componente
 - se calculeaza pretul si marginea
 
 - se permite ca in lista de materiale sa existe cantitati negative (recuperari)

    """,
    
    "category" : "Generic Modules/Production",
    "depends" : ['deltatech',"base","mrp","sale",'mrp_product_variants','sale_product_variants'],


    "data" : [  'wizard/take_bom_view.xml',
                'mrp_sale_view.xml',
                'mrp_view.xml' ,
                
                'views/report_saleorder.xml',
                'security/ir.model.access.csv',
             ],
    
    
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

