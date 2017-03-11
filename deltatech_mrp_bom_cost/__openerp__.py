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
#
##############################################################################

{
    "name": "Deltatech MRP BOM Cost",
    "version": "2.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:
 - Calculeaza pretul pentru fiecare lista de materiale
 - La fiecare bom exista posibilitatea de a defini costuri indirecte
 - In produs se memoreaza pretul caclulat in BOM
 
Obs: depinde si de mrp_product_variants
 
    """,

    "category": "Generic Modules/Production",
    "depends": ['deltatech', "base", "mrp_hook", "product_variants_no_automatic_creation"],

    "data": [
        "mrp_view.xml",
        "product_view.xml"

    ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
