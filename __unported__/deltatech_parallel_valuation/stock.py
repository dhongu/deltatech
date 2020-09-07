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

from odoo import models, fields, api, tools, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment


class stock_quant(models.Model):
    _inherit = "stock.quant"

    @api.one
    @api.depends('cost', 'qty', 'in_date')
    def _compute_parallel_inventory_value(self):
        date_eval = self.in_date or fields.Date.context_today(self)
        from_currency = self.env.user.company_id.currency_id.with_context(date=date_eval)
        to_currency = self.env.user.company_id.parallel_currency_id
        if to_currency:
            value = from_currency.compute(self._get_inventory_value(self), to_currency)
            self.parallel_inventory_value = value

    parallel_inventory_value = fields.Float(string="Parallel Inventory Value",
                                            digits=dp.get_precision('Product Price'),
                                            readonly=True, compute='_compute_parallel_inventory_value', store=True)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
