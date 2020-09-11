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
    "name" : "Deltatech Access at Records",
    "version" : "1.0",
    "author" : "Dorin Hongu",
    "category" : "Generic Modules",
    "depends" : ['deltatech',"product",'stock','sale','l10n_ro_stock_picking_report'],
 
    "description": """

Functionalitati:
 - Restrictionare acces la transfer stoc
 - Restrictionare acces la confirmare comanda de vanzare
 - Afisare stoc personal (dezactivat)
 - Afisare miscari personale (dezactivat)
 - Afisare quanturi proprii (dezactivat)
    """,
    "data" : [
         'security/security.xml',
         'stock_view.xml',
         'sale_view.xml',
         'res_users_view.xml'
    ],
    "active": False,
    "installable": True,
   
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
