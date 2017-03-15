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
    "name" : "Deltatech Print Invoice to ECR",
    "version" : "1.0",
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    'summary':'Generare fisier pentu casa de marcat',
    "description": """

Functionalitati:
 - Generare fisier pentru program de tiparit Bon Fiscal
 - definire client generic pentru care se fac in mod automat Bonuri fiscale

De pregatit:
 - Trebuie definit un jurnal de vanzari pentru Bonru Fiscale cu codul BF
   
    """,
    
    'category': 'Generic Modules',
    "depends" : ['deltatech',"account","web",'sale'],


 
    "data" : [ 'wizard/account_invoice_export_bf_view.xml',
               'wizard/sale_make_invoice_advance_views.xml',
               'data/data.xml'],
    
    "active": False,
    "installable": True,
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

