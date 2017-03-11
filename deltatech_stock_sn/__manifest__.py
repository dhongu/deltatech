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
    "name": "Deltatech Stock Serial Number",
    "version": "2.0",
    "author": "Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """
    
Functionalitati:

    - ascundere loturi utilizate
    - generare nr de lot la receptie daca se utilizeaza semnul /
    - generare certificat de garantie

    """,

    "category": "Generic Modules/Stock",
    "depends": ['deltatech', 'stock','l10n_ro_stock_picking_report'],

    "data": [
        'views/stock_view.xml',
        'views/stock_picking_report_view.xml',
        'views/product_view.xml'

    ],

    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
