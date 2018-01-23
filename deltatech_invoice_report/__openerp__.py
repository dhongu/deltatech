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
    "name" : "Deltatech Invoice Report",
    "version" : "1.0",
    "author": "Terrabit, Dorin Hongu",
    "website": "www.terrabit.ro",
    "description": """

Functionalitati: 
 -Adaugare in raportul de analiza facturi a campurilor: judet, nr de factura, furnizor si client

 In Produs a fost adaugat un buton pentru a vedea raportul de facturi in care se gaseste produsul cu pricina.


    """,
    "category" : "Generic Modules/Other",
    "depends": ['account', 'product'],

    "data": ['report/invoice_report_view.xml',
             'views/product_view.xml'],
    "active": False,
    "installable": True,
}


