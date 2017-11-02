# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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
    "name": "MRP Optimik",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:
----------------
Formate:

        Boards:
        Code = D | Mark of material | Quantity | Length | Width | = (Do not rotate – maintain the orientation) X (Any
        orientation) | Description | Set | Strip material mark
        
        Material:
        Code = M | Mark | Description | Minimum cut-off | Kerf | = (Oriented blister grain)
        X (Without the blister grain) | Minimum cut-off dimensions | Minimum length of large format sizes | Price
        Format:
        Code = F | Length | Width | + (to be used in the design) | | Mark
        Receipt/issue:
        Code = P | Date | Description | - (Issue) + (Receipt) | Quantity
        
        
        Job:
        Code = Z | Mark | Description | Date 
        
        Alte piese:
        Code = I | Mark | Description | Quantity | Set 
        
        Scrap:
        Code = X | Quantity
        
        Bucati care ramin 
        Code = O | Mark | Length | Width | Quantity
        

    """,

    "category": "Manufacturing",
    "depends": ["mrp","product_dimension","stock"],

    "data": [
        "wizard/mrp_optimik_export_view.xml",
        "wizard/mrp_optimik_import_view.xml",
        "views/mrp_bom_view.xml",
        "data/data.xml"
    ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
