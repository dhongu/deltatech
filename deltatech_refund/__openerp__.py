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
    "website": "www.terrabit.ro",

    "category": "Generic Modules/Stock",
    "depends": [
        'deltatech',
        "base",
        "stock",
        "purchase",
        "sale",
        'account',
       # 'deltatech_stock_report'  # am eliminat conditia pentru raport !!
    ],
    "license": "AGPL-3",
    "data": [
        'views/stock_return_picking_view.xml',
        'views/stock_view.xml',
        'views/account_invoice_view.xml',
        'views/res_config_view.xml',
    ],
    "active": False,
    "installable": True,
}
