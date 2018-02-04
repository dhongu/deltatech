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
    "name": "MRP Confirmation",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:
----------------
 - adaugare operatori la centre de lucru
 - adaugare cod la operatie
 - confirmare operatii prin scanare cod de bare
 

    """,

    "category": "Manufacturing",
    "depends": ['mrp', 'hr_attendance'],

    "data": [

        'views/mrp_confirmation_view.xml',

        'views/mrp_workcenter_view.xml',
        'views/mrp_workorder_view.xml',
        'views/mrp_routing_view.xml',
        'views/mrp_production_templates.xml',
        'views/mrp_rework_view.xml',
        'wizard/start_production_view.xml',
        'wizard/confirmation_view.xml',
        'wizard/mrp_mark_done_view.xml',
        'views/mrp_production_view.xml',
        'security/ir.model.access.csv',
        'views/web_asset_backend_template.xml',
        'data/data.xml',
    ],
    'qweb': [
        "static/src/xml/mrp.xml",
    ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
