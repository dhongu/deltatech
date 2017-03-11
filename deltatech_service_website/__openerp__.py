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
#
##############################################################################

{
    "name" : "Deltatech Services Website",
    "version" : "1.0",
    "author" : "Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:

- afisare in frontent a listei de echipamente
- introducere de citiri contori 
- afisare in frontend a listei de notificari
- adaugre sesizari
- afisare in frontend a listiei de comenzi
- semnare comanda
 
    """,
    
    "category" : "Generic Modules",
    "depends" : ["website",
                 "deltatech",
                 "deltatech_service",
                 "deltatech_service_equipment",
                 "deltatech_service_maintenance",
                 'deltatech_website_datatables',
                 ],


    "data" : [ 'data.xml',             
               'views/website_equipment.xml',
               'views/website_service.xml',
               'views/website_order.xml',
               'views/website_notification.xml',
                              
                ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

