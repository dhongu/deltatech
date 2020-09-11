# -*- coding: utf-8 -*-



import time
from odoo import api, models
from odoo.tools import formatLang



class ReportInvoicePrint(models.AbstractModel):
    _name = 'report.deltatech_invoice_print.report_invoice'
    _template = None

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(self._template)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'time': time,
            'docs': self.env[report.model].browse(docids),
            'with_discount': self._with_discount,
            'formatLang': self.formatLang
        }
        return report_obj.render(self._template, docargs)


    def formatLang(self, value, *args):
        return formatLang(self.env, value, *args)


    def _with_discount(self, invoice):
        res = False
        for line in invoice.invoice_line_ids:
            if line.discount != 0.0:
                res = True
        return res



class ReportInvoicePrint1(models.AbstractModel):
    _name = 'report.deltatech_invoice_print.report_invoice_1'
    _inherit = 'report.deltatech_invoice_print.report_invoice'
    _template = 'deltatech_invoice_print.report_invoice_1'


class ReportInvoicePrint2(models.AbstractModel):
    _name = 'report.deltatech_invoice_print.report_invoice_2'
    _inherit = 'report.deltatech_invoice_print.report_invoice'
    _template = 'deltatech_invoice_print.report_invoice_2'


