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
##############################################################################
{
    "name" : "Deltatech Products Alternative",
     'version': '10.0.1.0.0',
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "category" : "Generic Modules/Inventory Control",
    "depends" : ["product",'stock'],


    "description": """
Features:    
 - New model: product_catelog
 - A module that add alternative on the product form
 - Camp nou in produs (used for) pentru a indica la ce poate fi folosit produsul
 
 
""",
    "images": ['images/main_screenshot.png'], "license":"LGPL-3","data" : [
        "views/product_view.xml",
        'security/ir.model.access.csv',
    ],
    "active": False,
    "installable": True,
   
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
