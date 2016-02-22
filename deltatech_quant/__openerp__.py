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
    "name" : "Deltatech Quant",
    "version" : "1.0",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """

Functionalitati:
 - Afisare coloana de categorie produs in lista de pozitii de stoc
 - Adaugare client pentru pozitiile de stoc livrate care un partener
 - Adaugare furnizor pentru pozitiile de stoc achizitionate
 - Coloana cu numarul facturii de achiztiei 
 - Ofera posibilitatea de a modifica lotul unei pozitii de stoc
 
    """,
    
    
    "category" : "Generic Modules/Stock",
    "depends" : ['deltatech',"stock","account",
                 #"stock_picking_invoice_link"
                 ],
 
    "data" : [  
               'stock_view.xml',
               'wizard/stock_quant_change_lot_view.xml'
               ],
    
    "active": False,
    "installable": True,
}
 