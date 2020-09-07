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
    "name": "Deltatech Web Style",
    "version": "1.0",
    "author": "Dorin Hongu",
    "website": "",
    "description": """

Functionalitati:
 - Afisarea foilor din forme pe 90% din latimea ferestrei
 - Modificare butoane din rosu in albastru (new style din Odoo 9)
 - Modificare dimensiune H1 din 2em in 1.8em
 - adaugare afisare metadate in meniul Mai Multe 


    """,

    "category": "Generic Modules",
    "depends": ['deltatech', "web"],

    'data': ['views/deltatech_web_assets.xml'],




    "installable": True,
    'auto_install': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
