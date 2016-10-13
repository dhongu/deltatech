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
    "name" : "Deltatech SAGA Interface",
    "version" : "2.0",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """

Functionalitati:
 - Permite exportul de date din Odoo pentru a fi importate in Saga
 - Partenerii au doua referinte pentru codurile de client respectiv de furnizor din SAGA
 - categoriile de porduse au un camp nou pentru tipul de acticol din SAGA  
  
   
    """,
    
    "category" : "Generic Modules/Base",
    "depends" : ['deltatech','deltatech_account',"base","account","l10n_ro_invoice_report"],
    "external_depends":['dbf'],

 
    "data" : [
              'data.xml',
              'res_partner_view.xml',
              'product_view.xml',
              'wizard/export_saga_view.xml',
              #'wizard/import_saga_view.xml',
              ],
    
    "active": False,
    "installable": True,
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

