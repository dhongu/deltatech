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
    "name": "Deltatech Procurement",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "description": """
 
Features:
 - New fields in sale and purchase order: procurement_count, invoiced_rate
 - New buttons in sale and purchase order for display procurement order
 - New messages in log for procurement run. 

 - New menu for Stock Outgoing, Stock Internal Transfer, Stock Incoming
 - Trecerea de la make_to_order la make_to_stock
 - Afisare campuri de cantitate disponibila in comanda de vanzare
 - Daca produsul se compara atunci trebuie definit obligatoriu un furnizor
 - Pozitiile din lista de ridicare sunt editabile
 - Afisare locatie sursa in lista cu pozitiile din lista de ridicare

 - Filtru my pentru liste de ridicare
 - Adugare butone in comanda de vanzare,comanda de achzitie si lista de ridicare pentru consultare stoc cu pozitiile din document
 - Butonul Scrap Products este afisat doar la manager stoc
 - Anularea in masa a aprovizionarilor
 - Buton nou in lista de ridicare pentru validare operare transfer fizic 
 - Camap nou in comanda de vanzare pentru specificare date de livrare, date care sunt preluate in picking
 


    """,
    "category": "Generic Modules/Stock",
    "depends": ['deltatech',
                "base",
                "stock",
                "purchase",
                'procurement',
                'deltatech_required',
                'deltatech_show_quant',
                'deltatech_refund'],

    "data": ['views/purchase_view.xml',
              # 'required_product_view.xml',
              'views/sale_view.xml',
              'views/stock_view.xml',
              'views/procurement_view.xml',
              'wizard/procurement_change_status_view.xml',
             ],
    "active": False,
    "installable": True,
}
