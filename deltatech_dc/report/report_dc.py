# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

import time
from openerp.report import report_sxw
from openerp.osv import osv



class report_dc_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_dc_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'lot': False,
        })

class report_dc_lot_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_dc_lot_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'lot': True
        })


class report_dc_invoice_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_dc_invoice_print, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'lot': True,
        })

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = []
        for invoice in self.pool.get('account.invoice').browse(self.cr, self.uid, ids):
            for picking in invoice.picking_ids:
                for move in picking.move_lines:
                    for quant in move.quant_ids:
                        if quant.lot_id:
                            new_ids.append(quant.lot_id.id)

        objects = self.pool.get('stock.production.lot').browse(self.cr, self.uid, new_ids)
        return super(report_dc_invoice_print, self).set_context(objects, data, new_ids, report_type=report_type)
     
     
class report_dc(osv.AbstractModel):
    _name = 'report.deltatech_dc.report_dc'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_dc.report_dc'
    _wrapped_report_class = report_dc_print


class report_dc_lot(osv.AbstractModel):
    _name = 'report.deltatech_dc.report_dc_lot'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_dc.report_dc_lot'
    _wrapped_report_class = report_dc_lot_print
    

class report_dc_invoice(osv.AbstractModel):
    _name = 'report.deltatech_dc.report_dc_invoice'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_dc.report_dc_invoice'
    _wrapped_report_class = report_dc_invoice_print
        




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
