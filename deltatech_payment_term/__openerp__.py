# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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
    "name" : "Deltatech Payment Term Rate Wizard",
    "version" : "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:

  
   
    """,
    
    "category" : "Generic Modules/Base",
    "depends" : ['deltatech',"base","account","sale", 'deltatech_account'],
   


 
    "data" : [ 'wizard/payment_term_view.xml',
               "sale_view.xml",
               "account_view.xml",
               "account_invoice_view.xml",
               "res_partner_view.xml"
              ],
    
    "active": False,
    "installable": True,
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

