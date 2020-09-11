# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

import time

from odoo.report import report_sxw


class ExpensesDeductionReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(ExpensesDeductionReport, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({"time": time})


report_sxw.report_sxw(
    "report.deltatech.expenses.deduction.print",
    "deltatech.expenses.deduction",
    "addons/deltatech_expenses/report/expenses_deduction_report.rml",
    parser=ExpensesDeductionReport,
)
