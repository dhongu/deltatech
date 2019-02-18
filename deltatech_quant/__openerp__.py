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
##############################################################################
{
    "name": "Deltatech Quant",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati:
 - Afisare coloana de categorie produs in lista de pozitii de stoc
 - Adaugare client pentru pozitiile de stoc livrate care un partener
 - Adaugare furnizor pentru pozitiile de stoc achizitionate
 - Coloana cu numarul facturii de achiztiei 
 - Ofera posibilitatea de a modifica lotul unei pozitii de stoc
 - Permite impartirea unei pozitii de stoc
 - deschidere picking din miscarea de stoc
 
de facut:
 - Posibilitate de unire a pozitiilor de stoc
  
    """,

    "category": "Generic Modules/Stock",
    "depends": ['deltatech', "stock", "account",
                # "stock_picking_invoice_link"  # pentru a avea invoice_id in pickinglist
                ],

    "license": "LGPL-3", "data": [
        'stock_view.xml',
        'wizard/stock_quant_change_lot_view.xml',
        'wizard/stock_quant_split_view.xml',
        'security/ir.model.access.csv'
    ],

    "active": False,
    "installable": True,
}
