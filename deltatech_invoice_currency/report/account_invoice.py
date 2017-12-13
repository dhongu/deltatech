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


import time

from odoo.osv import osv
from odoo import api, models
from odoo.report import report_sxw
from odoo.tools import formatLang

class ReportInvoicePrint(models.AbstractModel):
    _name =  'report.deltatech_invoice_currency.report_invoice_0'
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
            'formatLang': self._formatLang
        }
        return report_obj.render(self._template , docargs)


    def _formatLang(self, value, *args):
        return formatLang(self.env, value, *args)


    def _with_discount(self, invoice):
        res = False
        for line in invoice.invoice_line_ids:
            if line.discount <> 0.0:
                res = True
        return res

class report_invoice_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_invoice_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'with_discount': self._with_discount,
            'formatLang': self._formatLang
        })

    def _formatLang(self, value, *args):
        return formatLang(self.env, value, *args)

    def _with_discount(self, invoice):
        res = False
        for line in invoice.invoice_line_ids:
            if line.discount != 0.0:
                res = True
        return res


class report_invoice_1(osv.AbstractModel):
    _name = 'report.deltatech_invoice_currency.report_invoice_1'
    _inherit = 'report.deltatech_invoice_currency.report_invoice_0' #'report.abstract_report'
    _template = 'deltatech_invoice_currency.report_invoice_1'
    _wrapped_report_class = report_invoice_print


class report_invoice_2(osv.AbstractModel):
    _name = 'report.deltatech_invoice_currency.report_invoice_2'
    _inherit = 'report.deltatech_invoice_currency.report_invoice_0'#'report.abstract_report'
    _template = 'deltatech_invoice_currency.report_invoice_2'
    _wrapped_report_class = report_invoice_print

