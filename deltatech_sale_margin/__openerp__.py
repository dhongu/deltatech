# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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
    "name" : "Deltatech Sale Margin",
    "version" : "1.0",
    "category" : "Sales Management",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """
 
Sale Margin  
 - New technical access group for display margin and purchase price in sale order
 - New technical access group to prevent changing price in sale order
 - Warning on sale order if sale price is below the purchase price

    """,
    
    "depends" : ["sale_margin"],
 
    "data" : ['security/sale_security.xml','security/ir.model.access.csv','sale_margin_view.xml','account_invoice_view.xml'],
    "active": False,
    "installable": True,
}


