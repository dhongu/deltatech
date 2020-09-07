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
    "name": "Deltatech Stock Pack",
    'version': '10.0.1.2.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "description": """
    
Functionalitati:

    - transferare packet intregral dintr-o locatie in alta
    - generare automata de pachete in functie de catitatea maxima din masterul de produs
    - editare greutate
    

    """,

    "category": "Generic Modules/Stock",
    "depends": ['stock', "sale", "account"],


    "data": [
        'wizard/pack_transfer_view.xml',
               # 'wizard/stock_transfer_details_view.xml',
        'stock_view.xml',
        'product_view.xml',
        'views/report_invoice.xml'
    ],


    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
