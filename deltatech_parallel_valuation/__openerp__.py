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
    "name" : "Deltatech Parallel Valuation",
    "version" : "1.0",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """

Functionalitati:
 - Definire moneda paralela de evaluare si raportare
 - Evaluarea  stocului in moneda paralela
 - Afisare curs valutar in moneda paralela
 - Raport de stoc valorinc exprimat in moneda paralela la data curenta
 - Camp pentru curs valutar in factura
 - Data facturii  editabila si in cazul in care factura este in starea proforma
 - Nume/referinta factura  editabil si in cazul in care factura este in starea proforma
 
    """,
    
    
    "category" : "Generic Modules/Stock",
    "depends" : ['deltatech',"account","stock_account",'l10n_ro_stock_account','deltatech_sale_margin','l10n_ro_invoice_report'],
 
    "data" : [ 'res_config_view.xml',
               'stock_valuation_history_view.xml',
               'stock_view.xml',
               'views/invoice_report.xml',
               'product_view.xml',
               'account_invoice_view.xml'
               ],
    
    "active": False,
    "installable": True,
}
 