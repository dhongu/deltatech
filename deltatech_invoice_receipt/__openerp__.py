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
    "name": "Deltatech Invoice Receipt",
    'version': '10.0.1.0.0',
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati: 
 - Adaugare buton nou in factura de receptie care  genereaza document de receptie stocuri  
 - Nu se permite achizitia unui produs stocabil fara comanda aprovizionare (picking in asteptare).
 - La creare factura din picking se face ajustarea automata a monedei de facturare in conformitate cu moneda din jurnal 
 - Adaugat buton pentru a genera un picking in asteptare in conformitate cu liniile din factura
 - Se permite generarea unei document de recepție pentru produsele care nu au comanda de achizitie
 - Pretul produselor se actualizeaza automat pentru receptiile fara comanda de achizitie
 - Furnizorul produselor se actualizeaza automat pentru receptiile fara comanda de achizitie 

 - Calcul pret produs in functie de lista de preturi aferenta clientului/furnizorului

Antentie:
 - la inregistrarea facturilor in care sunt un produs apare de mai multe ori cu preturi diferite!


    """,
    "category": "Accounting",
    "depends": [
        'deltatech_backwards',
        'deltatech_stock_date',
        "base",
        "stock",
        "account",
        "purchase",
        'deltatech_refund',
        # "deltatech_stock_reverse_transfer",
        # "stock_picking_invoice_link"
    ],

    "data": [
        'account_invoice_view.xml'
    ],
    "active": False,
    "installable": True,
}
