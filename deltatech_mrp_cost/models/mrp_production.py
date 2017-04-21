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


class MrpProduction(models.Model):
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
                planned_cost = False  # nu ao fost facute miscari de stoc

        if planned_cost:
            for move in production.move_raw_ids:
                for quant in move.reserved_quant_ids:
                    if quant.qty > 0:
                        amount += quant.cost * quant.qty  # se face calculul dupa quanturile planificate
            calculate_price = amount / production.product_qty
            amount = 0.0  # pretul poate fi caclulat dar valoarea productie va fi la final
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
        super(MrpProduction, self)._cal_price(consumed_moves)
        self.ensure_one()
        production = self
        production.assign_picking()
        if production.product_id.cost_method == 'real' and production.product_id.standard_price != production.calculate_price:
            # oare aici am campul calculate_price actualizat dupa miscarile de stoc efectuate?
            production.product_id.write({'standard_price': production.calculate_price})
        return True

    @api.multi
    def _generate_moves(self):
        res = super(MrpProduction, self)._generate_moves()
        self.assign_picking()
        return res

    @api.multi
    def assign_picking(self):
        """
        Totate produsele consumate se vor reuni intr-un picking list (Bon de consum)
        """
        for production in self:
            move_list = self.env['stock.move']
            picking = False
            for move in production.move_raw_ids:
                if not move.picking_id:
                    move_list += move
                else:
                    picking = move.picking_id
            if move_list:
                picking_type = self.env.ref('stock.picking_type_consume', raise_if_not_found=False)
                if not picking_type:
                    picking_type = self.env.ref('stock.picking_type_internal', raise_if_not_found=False)

                if picking_type:
                    if not picking:
                        picking = self.env['stock.picking'].create({'picking_type_id': picking_type.id,
                                                                    'date': production.date_planned_start,
                                                                    'location_id':picking_type.default_location_src_id.id,
                                                                    'location_dest_id':picking_type.default_location_dest_id.id,
                                                                    'origin': production.name})
                    move_list.write({'picking_id': picking.id})
                    # picking.get_account_move_lines()  # din localizare

        return
