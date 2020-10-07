# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    parallel_stock_value = fields.Float(string="Parallel Stock Value", digits= dp.get_precision('Product Price'), readonly=True, )       
    parallel_line_value = fields.Float(string="Parallel Line Value", digits= dp.get_precision('Product Price'), readonly=True, )  

    def _select(self):
        return  super(AccountInvoiceReport, self)._select() + ", parallel_stock_value, parallel_line_value "

    def _sub_select(self):
        return  super(AccountInvoiceReport, self)._sub_select() +  """,
                        SUM(CASE
                         WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN - COALESCE( parallel_stock_value, parallel_line_value )
                            ELSE   COALESCE( parallel_stock_value, parallel_line_value )
                        END) AS parallel_stock_value,
                        SUM(CASE
                         WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN - parallel_line_value
                            ELSE parallel_line_value
                        END) AS parallel_line_value
                    """



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
