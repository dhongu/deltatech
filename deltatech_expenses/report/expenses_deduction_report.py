# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

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
