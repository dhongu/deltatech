# -*- coding: utf-8 -*-

import time

from odoo.osv import osv
from odoo.report import report_sxw


class report_invoice_warranty(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_invoice_warranty, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'warranty_text': self._get_warranty_text
        })

    def _get_warranty_text(self, product_id):
        categ = product_id.categ_id
        while categ and not categ.warranty_header:
            categ = categ.parent_id

        return {'categ': categ}


class report_invoice(osv.AbstractModel):
    _name = 'report.deltatech_stock_sn.report_invoice_warranty'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_stock_sn.report_invoice_warranty'
    _wrapped_report_class = report_invoice_warranty
