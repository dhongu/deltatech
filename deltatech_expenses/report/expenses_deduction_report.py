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
##############################################################################

import time
from odoo.report import report_sxw

class expenses_deduction_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(expenses_deduction_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })
        
report_sxw.report_sxw(
    'report.deltatech.expenses.deduction.print',
    'deltatech.expenses.deduction',
    'addons/deltatech_expenses/report/expenses_deduction_report.rml',
    parser=expenses_deduction_report
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
