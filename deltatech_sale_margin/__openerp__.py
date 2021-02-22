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
    "name" : "Deltatech Sale Margin",
    "version" : "1.0",
    "category" : "Sales Management",
    "author" : "Dorin Hongu",
    "website" : "",
    "description": """
 
Features:
 - New technical access group for display margin and purchase price in sale order and customer invoice
 - New technical access group to prevent changing price in sale order (and customer invoice) 
 - New technical access group to allow sale price  below the purchase price
 - Warning/Error on sale order if sale price is below the purchase price
 - Warning/Error on customer invoice if sale price is below the purchase price
 - New report for analysis profitability
 - Calcul comisione de vanzari
 - Pretul de vanzare este fara TVA calculat prin modulul l10n_ro_invoice_report

    """,
    
    "depends" : ['deltatech',"sale_margin",'account',
                 #'l10n_ro_invoice_report'
                 ],
 
    "data" : ['security/sale_security.xml',
              'security/ir.model.access.csv',
              'sale_margin_view.xml',
              'account_invoice_view.xml',
              'report/sale_margin_report.xml',
              'commission_users_view.xml',
              'wizard/commission_compute_view.xml',
              'wizard/update_purchase_price_view.xml'

              ],
              
    "active": False,
    "installable": True,
}


