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
    "name" : "Deltatech Payment On Delivery",
    "version" : "2.0",
    "author": "Terrabit, Dorin Hongu",
    "website" : "",
    "description": """
    
Functionalitati:
 - plata la livrare

    """,
    
    "category" : "Sales Management",
    "depends" : ['deltatech','sale','payment','delivery','website_sale'],


    "data" : [  'views/on_delivery.xml','data.xml',
              'sale_view.xml',
              'payment_view.xml','account_invoice_view.xml',
             ],
    
    
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

