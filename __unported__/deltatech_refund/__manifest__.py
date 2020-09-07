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
    "name": "Deltatech Refund",
    "version": "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",
    "description": """




Functionalitati: 
 - Adaugate campuri in lista de ridicare pentru rambursare si pt documentul rambursat
 - La o rambursare se poate genera o noua rambursare in asteptare
 - Documentul de rambursare se poate inregistra in mod automat 
 - La anularea unei factrui se va vor aula in mod automat si miscarile de stoc aferente.
 - La stergerea unei facturi se va schimba si starea picking listului
 - dupa anularea unei facturi se poate actiona un buton pentru a rambursa operatiile de stoc
 - in lista de ridicari sunt afisate rambursarile cu gri si italic

    """,
    "category": "Generic Modules/Stock",
    "depends": ['deltatech',
                "base",
                "stock",
                "purchase",
                "sale",
                'account',
                'deltatech_stock_report'],

    "data": [
        'views/stock_return_picking_view.xml',
              'views/stock_view.xml',
              'views/account_invoice_view.xml',
              'views/res_config_view.xml',
    ],
    "active": False,
    "installable": True,
}
