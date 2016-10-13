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
#
##############################################################################

{
    "name" : "Deltatech Services",
    "version" : "1.0",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """

Functionalitati:
 - Ofera posibilitatea de a defini contracte de servicii.
 - Periodic in baza acestor contracte se genereaza facturi.

 
    """,
    
    "category" : "Service Management",
    "depends" : ["base", "product","account","deltatech_backwards"],


    "data" : [ 
              'data/data.xml',
              "views/service_consumption_view.xml",
              "views/service_agreement_view.xml",
              
              "wizard/service_billing_preparation_view.xml",
              "wizard/service_billing_view.xml",
              "wizard/service_distribution_view.xml",
              "wizard/service_price_change_view.xml",
              "wizard/service_change_invoice_date_view.xml",
              #"views/account_invoice_penalty_view.xml",
              'security/service_security.xml',
              'security/ir.model.access.csv',
              
                ],
    'application': True,
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

