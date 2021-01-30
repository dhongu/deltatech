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
    "name": "Deltatech Price: Bronze Silver Gold Platinum",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Adaugare a 4 campuri in produs pentru 4 categorii de pret:
    1. pret bronz
    2. pret silver
    3. pret gold
    4. pret platinum
 
 

    """,

    "category": "Generic Modules/Stock",
    "depends": ['deltatech', "product",'account'],

    "license": "AGPL-3",
    "data": ['product_view.xml',
             ],

    "active": False,
    "installable": True,
}
