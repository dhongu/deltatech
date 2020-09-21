# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2014 Deltatech All Rights Reserved
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
#
##############################################################################


import time
from odoo.report import report_sxw
from odoo.osv import osv

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
        if qty <> 0:
            res['price'] = amount / qty
        res['amount'] = -1 * amount
        return res

class report_mrp_order(osv.AbstractModel):
    _name = 'report.deltatech_mrp.report_mrp_order'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_mrp.report_mrp_order'
    _wrapped_report_class = report_mrp_order_wrapped


