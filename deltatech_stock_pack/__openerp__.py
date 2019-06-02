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
    "name": "Stock Pack",
    "version": "2.1",
    "author": "Terrabit, Dorin Hongu",
    "website": "https://www.terrabit.ro",


    "category": "Stock",
    "depends": [
        'stock',
        "sale",
        "account",
        'terrabit_product_labels'
    ],

    "license": "AGPL-3",
    "data": [
        'wizard/pack_transfer_view.xml',
        'wizard/stock_transfer_details_view.xml',
        'views/stock_view.xml',
        'views/product_view.xml',
        'views/account_invoice_view.xml',
        'views/report_invoice.xml',
        'views/bom_view.xml',
        'security/ir.model.access.csv',
    ],

    "active": False,
    "installable": True,
}




