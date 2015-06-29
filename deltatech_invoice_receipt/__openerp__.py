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
    "name" : "Deltatech Invoice Receipt",
    "version" : "1.0",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """
 
Adaugare buton nou in factura de receptie care  genereaza document de receptie stocuri  

Nu se permite achizitia unui produs stocabil fara comanda aprovizionare

La creare factura din picking se face ajustarea automata a monedei de facturare in conformitate cu moneda din jurnal 

Validare data factura sa fie mai mare decat data din ultima factura

Antentie la inregistrarea facturilor in care sunt un produs apare de mai multe ori cu preturi diferite!


    """,
    "category" : "Generic Modules/Other",
    "depends" : ['deltatech',"base","stock","account","purchase","stock_picking_invoice_link"],
 
    "data" : [ 'account_invoice_view.xml'],
    "active": False,
    "installable": True,
}


