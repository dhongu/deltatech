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
    "name" : "Deltatech Sale Report",
    "version" : "1.0",
    "author" : "Deltatech",
    "website" : "",
    "description": """
Sale report
===========

Sales report presents the profitability analysis.

sale.order.line
    - modificat metoda button_confirm - actualizare a pretului de vânzare daca pretul este = 1.

    """,
    "category" : "Generic Modules",
    "depends" : ["base","sale","sale_stock"],


    "data" : [       'security/ir.model.access.csv',
                     "report/deltatech_sale_report.xml"
                     ],
    "active": False,
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

