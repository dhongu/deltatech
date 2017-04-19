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

import odoo.addons.decimal_precision as dp

from odoo import api
from odoo import models, fields


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    amount = fields.Float(digits=dp.get_precision('Account'), string='Production Amount', compute='_calculate_amount')
    calculate_price = fields.Float(digits=dp.get_precision('Account'), string='Calculate Price',
                                   compute='_calculate_amount')

    @api.one
    def _calculate_amount(self):
        production = self
        calculate_price = 0.0
        amount = 0.0

        planned_cost = True
        for move in production.move_raw_ids:
            if move.quantity_done > 0:
                planned_cost = False

        if planned_cost:
            for move in production.move_raw_ids:
                for quant in move.reserved_quant_ids:
                    if quant.qty > 0:
                        amount += quant.cost * quant.qty  # se face calculul dupa quanturile planificate
            calculate_price = amount / production.product_qty
            amount = 0.0
        else:
            for move in production.move_raw_ids:
                for quant in move.quant_ids:
                    if quant.qty > 0:
                        amount += quant.cost * quant.qty
            product_qty = 0.0
            for move in production.move_finished_ids:
                product_qty += move.product_uom_qty
            if product_qty == 0.0:
                product_qty = production.product_qty
            calculate_price = amount / product_qty

        production.calculate_price = calculate_price
        production.amount = amount



    def _cal_price(self, consumed_moves):
        self.ensure_one()
        production = self
        if production.product_id.cost_method == 'real' and production.product_id.standard_price <> production.calculate_price:
            production.product_id.write({'standard_price': production.calculate_price})
        return True






