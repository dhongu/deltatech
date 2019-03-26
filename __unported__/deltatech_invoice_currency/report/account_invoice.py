# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import time
from odoo import api, models
from odoo.tools import formatLang

class ReportInvoicePrint(models.AbstractModel):
    _name =  'report.deltatech_invoice_currency.report_invoice_0'
    _template = None


    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(self._template)
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'time': time,
            'docs': self.env[report.model].browse(docids),

            'with_discount': self._with_discount,
            'formatLang': self._formatLang
        }

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']

        docargs = self._get_report_values()
        return report_obj.render(self._template, docargs)



    def _formatLang(self, value, *args):
        return formatLang(self.env, value, *args)


    def _with_discount(self, invoice):
        res = False
        for line in invoice.invoice_line_ids:
            if line.discount != 0.0:
                res = True
        return res



class report_invoice_1(ReportInvoicePrint):
    _name = 'report.deltatech_invoice_currency.report_invoice_1'
    _inherit = 'report.deltatech_invoice_currency.report_invoice_0'
    _template = 'deltatech_invoice_currency.report_invoice_1'


class report_invoice_2(ReportInvoicePrint):
    _name = 'report.deltatech_invoice_currency.report_invoice_2'
    _inherit = 'report.deltatech_invoice_currency.report_invoice_0'
    _template = 'deltatech_invoice_currency.report_invoice_2'


