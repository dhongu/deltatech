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
    "name": "Deltatech Stock Inventory",
    "version": "1.0",
    "author" : "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

     Afisare coloana de pret de stoc la inventariere
     Afisare valoare de vanzare in rapotul de pozitii de stoc (evaluare inventar) si stoc la data
 
    """,
    "category": "Generic Modules/Other",
    "depends": ['deltatech', 'deltatech_stock_date', "stock_account"],

    "data": [
        'data/data.xml',
        'views/stock_view.xml',
        'views/product_view.xml',
        'views/report_stockinventory.xml'
    ],
    "active": False,
    "installable": True,
}
