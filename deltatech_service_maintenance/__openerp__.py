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
    "name": "Deltatech Services Maintenance",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:

- gestionare sesizari
- gestionare comenzi de service
- gestionare planuri de revizii
- generare automat a comenzilor de service in baza planului




 
    """,

    "category": "Generic Modules",
    "depends": ["base", "mail", "stock",

                "deltatech_service",
                "deltatech_service_equipment",
                "deltatech_procurement",
                "deltatech_product_extension",
                "deltatech_stock_report",
                "web_notification",  # pentru afisare mesaje procese lansate in background
                ],

    "license": "AGPL-3", "data": [

        'security/service_security.xml',
        'data.xml',

        'service_config_view.xml',
        'service_notification_view.xml',
        'service_order_view.xml',
        'service_plan_view.xml',

        'service_equipment_view.xml',
        'stock_view.xml',
        'sale_view.xml',
        'security/ir.model.access.csv',

    ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
