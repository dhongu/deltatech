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
    "name" : "Deltatech Mentor Interface",
    "version" : "2.0",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """

Functionalitati:
 - Permite exportul de date din Odoo pentru a fi importate in Mentor
   
Documentatia Mentor de import  din alte aplicatii
http://download.winmentor.ro/WinMentor/Documentatie/08_Structuri%20import%20din%20alte%20aplicatii/   
   
    """,
    
    "category" : "Generic Modules/Base",
    "depends" : ['deltatech',"base"],


 
    "data" : [
              'views/report_product.xml',
              'views/report_invoice.xml',
              'views/report_partner.xml',
              'wizard/export_mentor_view.xml'
              ],
    
    "active": False,
    "installable": True,
}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

