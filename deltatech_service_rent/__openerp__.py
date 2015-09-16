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
    "name" : "Deltatech Services Rent",
    "version" : "1.0",
    "author" : "Deltatech",
    "website" : "",
    "description": """

Functionalitati:

- gestionare echipamente
- gestionare contoare  
- gestionare citiri contoare
- facturare in baza citirilor
- caclul estimat 
- intoducere automat la sfarsit de perioada a valorilor estimate

- gestionare sesizari
- gestionare comenzi de service
- gestionare planuri de revizii
- generare automat a comenzilor de service in baza planului

- gestionare consumabile pentru un echipament

- raport calcul eficienta echipamente
 
    """,
    
    "category" : "Generic Modules",
    "depends" : ["base","website","mail",
                 "deltatech",
                 "deltatech_service",
                 "deltatech_procurement",
                 "deltatech_product_extension",
                 "deltatech_stock_report",
                 "web_notification",   #pentru afisare mesaje procese lansate in background
                 'deltatech_website',
                 ],


    "data" : [ 'data.xml',
              
               'service_rent_view.xml',
               'service_notification_view.xml',
               'service_efficiency_report.xml',
               'stock_view.xml',
               'security/service_security.xml',
               'security/ir.model.access.csv',
               

               
               'service_order_view.xml',
               'service_meter_view.xml',
               'service_equipment_view.xml',
               'service_consumable_view.xml',
               'service_plan_view.xml',
               
               'wizard/estimate_view.xml',
               'wizard/rescheduling_view.xml',
               'wizard/enter_readings_view.xml',
               
               'views/website_equipment.xml',
               'views/website_service.xml',
               'views/website_order.xml',
               'views/website_notification.xml',
                              
                ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

