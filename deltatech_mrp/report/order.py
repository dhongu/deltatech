# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details


import time
from openerp.report import report_sxw
from openerp.osv import osv

class report_mrp_order_wrapped(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_mrp_order_wrapped, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_line':self._get_line,
        })

    def _get_line(self,move_line):
        res = {'price':0.0, 'amount':0.0}
        amount = 0
        qty = 0
        for quant in move_line.quant_ids:
            if quant.location_id.usage == 'internal':
                amount +=  quant.cost * quant.qty
                qty += quant.qty
        if qty != 0:
            res['price'] = amount / qty
        res['amount'] = -1 * amount
        return res

class report_mrp_order(osv.AbstractModel):
    _name = 'report.deltatech_mrp.report_mrp_order'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_mrp.report_mrp_order'
    _wrapped_report_class = report_mrp_order_wrapped

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
