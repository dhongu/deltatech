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
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:
 - Se permite intocmirea unei liste de produse in comanda de vanzare
 - In lista de produse se pot defini atribute
 - se face explozia listei initiale in a lista de componente
 - se calculeaza pretul si marginea
 
 - se permite ca in lista de materiale sa existe cantitati negative (recuperari)
 
 - se permite editarea manuala a atibutelor unui produs
 - se pot defini valori implicite la atribute - preluate in comanda de vanzare
 
 - se permite adaugarea unei margini pe fiecare pozitie 
 - rapoarte:
     - 3 variante export
     - raport grupat pe other_category

    """,
    
    "category" : "Generic Modules/Production",
    "depends" :
        ["mrp",
         "sale",
         'mrp_product_variants',
         'sale_product_variants',
                 'deltatech',
                 'deltatech_mrp_bom_cost',
                 'deltatech_percent_qty'],

    "license": "AGPL-3",
    "data" : [  'wizard/take_bom_view.xml',
                'wizard/sale_add_margin_view.xml',
                'mrp_sale_view.xml',
                'mrp_view.xml' ,
                'product_view.xml',
                'views/report_saleorder.xml',
                'views/report_saleorder_v1.xml',
                'views/report_saleorder_v2.xml',
                'views/report_saleorder_v3.xml',
                'views/report_saleorder_group.xml',
                'views/simple_products.xml',
                'security/ir.model.access.csv',
                'views/report_saleorder_sia.xml',
                'views/report_saleorder_v5.xml',
                'resource_convert_view.xml'
             ],
    
    
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

