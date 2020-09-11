# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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
    "name": "Deltatech Pozitii Stoc",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "description": """

Functionalitati:
----------------

 - Afisare coloana de categorie produs in lista de pozitii de stoc
 - Adaugare client pentru pozitiile de stoc livrate care un partener
 - Adaugare furnizor pentru pozitiile de stoc achizitionate
 - Coloana cu numarul facturii de achiztiei 
 - Ofera posibilitatea de a modifica lotul unei pozitii de stoc
 - Permite impartirea unei pozitii de stoc
 - Raport de profit obtinut din pozitiile de stoc
 
de facut:
 - Posibilitate de unire a pozitiilor de stoc
  
    """,

    "category": "Generic Modules/Stock",
    "depends": [

        "stock",
        "point_of_sale",
        "account",
        "deltatech_product_extension",
        # "stock_picking_invoice_link"
    ],

    "data": [
        'views/stock_view.xml',
        'views/stock_profit_view.xml',
        'wizard/stock_quant_change_lot_view.xml',
        'wizard/stock_quant_split_view.xml',
        'security/ir.model.access.csv'
    ],

    "active": False,
    "installable": True,
}
