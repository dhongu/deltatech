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
##############################################################################




import time
from odoo.report import report_sxw
from odoo.osv import osv


class picking_delivery(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(picking_delivery, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'warranty_text':self._get_warranty_text
        })


    def _get_warranty_text(self,product_id):

        categ = product_id.categ_id
        while categ and not categ.warranty_header:
            categ = categ.parent_id

        return {'categ':categ}

class report_delivery(osv.AbstractModel):
    _name = 'report.deltatech_stock_sn.report_warranty'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_stock_sn.report_warranty'
    _wrapped_report_class = picking_delivery




"""

import time
from odoo import api, models

class report_delivery(models.AbstractModel):
    _name = 'report.deltatech_stock_sn.report_warranty'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('deltatech_stock_sn.report_warranty')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'time': time,
            'warranty_text': self._get_warranty_text
        }
        return report_obj.render('deltatech_stock_sn.report_warranty', docargs)


    def _get_warranty_text(self,product_id):

        categ = product_id.categ_id
        while categ and not categ.warranty_header:
            categ = categ.parent_id

        return {'categ':categ}
"""

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
