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
    "name": "Deltatech Services Equipment",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:

- gestionare echipamente
- gestionare contoare  
- gestionare citiri contoare
- facturare in baza citirilor
- caclul estimare citiri
- intoducere automat la sfarsit de perioada a valorilor estimate
- generare echipamnte din pozitii de stoc

- gestionare consumabile pentru un echipament

- raport calcul eficienta echipamente
 
    """,

    "category": "Generic Modules",
    "depends": ["base", "mail",

                "deltatech_service",
                "deltatech_procurement",
                "deltatech_product_extension",
                "deltatech_stock_report",
                "web_notification",  # pentru afisare mesaje procese lansate in background
                ],

    "data": ['data.xml',
             'service_config_view.xml',
             'service_rent_view.xml',

             'service_efficiency_report.xml',
             'stock_view.xml',
             'security/service_security.xml',
             'security/ir.model.access.csv',

             'wizard/estimate_view.xml',
             'wizard/enter_readings_view.xml',
             'wizard/service_equi_operation_view.xml',
             'wizard/service_equi_agreement_view.xml',
             'wizard/new_equi_from_quant_view.xml',

             'service_meter_view.xml',
             'service_equipment_view.xml',
             #  'service_consumable_view.xml',

             'demo.xml',
             # 'service.meter.reading.csv'

             ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
