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

from odoo import models, fields, api, tools, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment


class sale_margin_report(models.Model):
    _inherit = "sale.margin.report"

    parallel_stock_value = fields.Float(string="Parallel Stock Value", digits=dp.get_precision('Product Price'), readonly=True,
                                        help="Stock value in parallel currency evaluated at purchasing")
    parallel_line_value = fields.Float(string="Parallel Line Value", digits=dp.get_precision('Product Price'), readonly=True,
                                       help="Sale value in parallel currency evaluated at invoicing")
    parallel_profit = fields.Float(string="Parallel Profit", digits=dp.get_precision('Product Price'), readonly=True,
                                   help="Profit obtained at invoicing in parallel currency")

    def _select(self):
        select_str = super(sale_margin_report, self)._select()
        select_str = select_str + """
            ,  parallel_stock_value  ,   parallel_line_value , parallel_profit
        """
        return select_str

    def _sub_select(self):
        select_str = super(sale_margin_report, self)._sub_select()
        select_str = select_str + """
            , sum(parallel_stock_value) as parallel_stock_value 
            , sum(parallel_line_value) as parallel_line_value
            , sum(parallel_line_value-parallel_stock_value) as parallel_profit
        """

        return select_str

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
