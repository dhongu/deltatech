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
    "name": "Deltatech Claim 8D",
    "version": "1.0",
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 -Raportare 8D
  
  https://en.wikipedia.org/wiki/Eight_Disciplines_Problem_Solving
  
   
    """,

    'category': 'Sales Management',
    "depends": [
        'deltatech',
        'product',
        "deltatech_simple_crm_claim"
    ],

    "data": [
        'security/ir.model.access.csv',
        'views/report8d.xml',
        'views/crm_claim_view.xml'
    ],

    'installable': True,
    'auto_install': False,
}
