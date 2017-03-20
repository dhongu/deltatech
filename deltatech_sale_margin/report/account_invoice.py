# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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

"""
from openerp import api, models

class InvoicePrintReport(models.AbstractModel):
    _name = 'report.deltatech_sale_margin.report_invoice_nir'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('deltatech_sale_margin.report_invoice_nir')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'time': time,
            'with_discount': self._with_discount,
        }
        return report_obj.render('deltatech_sale_margin.report_invoice_nir', docargs)

    def _with_discount(self, invoice):
        res = False
        for line in invoice.invoice_line:
            if line.discount != 0.0:
                res = True
        return res


"""

from openerp.report import report_sxw
from openerp.osv import osv


class report_invoice_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_invoice_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'with_discount': self._with_discount,
            'get_line': self._get_line,
        })

    def _with_discount(self, invoice):
        res = False
        for line in invoice.invoice_line:
            if line.discount != 0.0:
                res = True
        return res

    def _get_line(self, line):
        res = {'price': 0.0, 'amount': 0.0, 'tax': 0.0, 'amount_tax': 0.0, 'sale_price': 0.0}

        cur_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        cur = line.invoice_id.currency_id
        tocur = line.company_id.currency_id

        taxes = tax_obj.compute_all(self.cr, self.uid, line.product_id.supplier_taxes_id, line.purchase_price,
                                    line.quantity, line.product_id)

        res['amount'] = cur_obj.round(self.cr, self.uid, cur, taxes['total'])
        if line.quantity != 0:
            res['price'] = cur_obj.round(self.cr, self.uid, cur, taxes['total']) / line.quantity
        else:
            res['price'] = 0.0

        res['tax'] = cur_obj.round(self.cr, self.uid, cur, taxes['total_included'] - taxes['total'])
        res['amount_tax'] = cur_obj.round(self.cr, self.uid, cur, taxes['total_included'])

        # pretul calculat in moneda companiei
        price_unit = cur_obj.compute(self.cr, self.uid, cur.id, tocur.id, line.price_unit,
                                     context={'date': line.invoice_id.date_invoice})
        print "Convert from %s to %s: %s -> %s" % (cur.name, tocur.name, str(line.price_unit), str(price_unit))
        res['sale_price'] = price_unit

        taxes_sale = tax_obj.compute_all(self.cr, self.uid, line.invoice_line_tax_id, price_unit,
                                         line.quantity, line.product_id)
        res['amount_sale'] = cur_obj.round(self.cr, self.uid, cur, taxes_sale['total_included'])
        if taxes['total_included'] != 0.0:
            res['margin'] = 100 * (taxes_sale['total_included'] - taxes['total_included']) / taxes['total_included']
        else:
            res['margin'] = 0.0

        return res


class report_invoice_nir(osv.AbstractModel):
    _name = 'report.deltatech_sale_margin.report_invoice_nir'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_sale_margin.report_invoice_nir'
    _wrapped_report_class = report_invoice_print

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
