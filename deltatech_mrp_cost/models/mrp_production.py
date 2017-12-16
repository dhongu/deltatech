 # -*- coding: utf-8 -*-
# ©  2015-2017 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details



import odoo.addons.decimal_precision as dp

from odoo import api
from odoo import models, fields
import math



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
                planned_cost = False  # nu au fost facute miscari de stoc

        if planned_cost:
            for move in production.move_raw_ids:
                if move.reserved_quant_ids:
                    for quant in move.reserved_quant_ids:
                        if quant.qty > 0:
                            qty = quant.qty + quant.qty * quant.product_id.scrap
                            amount += quant.cost *  qty  # se face calculul dupa quanturile planificate
                else:
                    qty = move.product_qty + move.product_qty * move.product_id.scrap
                    amount += move.product_id.standard_price * qty
            product_qty = production.product_qty

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

        # adaugare manopera:

        if production.routing_id:
            for operation in production.routing_id.operation_ids:
                time_cycle = operation.get_time_cycle(quantity=product_qty, product=production.product_id)

                cycle_number = math.ceil(product_qty / operation.workcenter_id.capacity)
                duration_expected = (operation.workcenter_id.time_start +
                                     operation.workcenter_id.time_stop +
                                     cycle_number * time_cycle * 100.0 / operation.workcenter_id.time_efficiency)

                amount += (duration_expected / 60) * operation.workcenter_id.costs_hour

        calculate_price = amount / product_qty
        production.calculate_price = calculate_price

        if not planned_cost:
            production.amount = amount

    def _cal_price(self, consumed_moves):
        super(MrpProduction, self)._cal_price(consumed_moves)
        self.ensure_one()
        production = self
        if production.product_id.cost_method == 'real' and production.product_id.standard_price != production.calculate_price:
            # oare aici am campul calculate_price actualizat dupa miscarile de stoc efectuate?
            price_unit = production.calculate_price
            production.product_id.write({'standard_price': price_unit})
            production.move_finished_ids.write({'price_unit': price_unit})
        return True

    @api.multi
    def post_inventory(self):
        self.assign_picking()
        return super(MrpProduction, self).post_inventory()

    @api.multi
    def _generate_moves(self):
        res = super(MrpProduction, self)._generate_moves()
        self.assign_picking()
        return res

    @api.multi
    def assign_picking(self):
        """
        Toate produsele consumate se vor reuni intr-un picking list (Bon de consum)
        toate produsele receptionate (de regula un singur produs) se vor reuni intr-un picking list (Nota de predare)
        """
        for production in self:
            # bon de consum
            move_list = self.env['stock.move']
            picking = False
            for move in production.move_raw_ids:
                if not move.picking_id:
                    move_list += move
                else:
                    picking = move.picking_id
            if move_list:
                picking_type = self.env.ref('stock.picking_type_consume', raise_if_not_found=True)

                if picking_type:
                    if not picking:
                        picking = self.env['stock.picking'].create({'picking_type_id': picking_type.id,
                                                                    'date': production.date_planned_start,
                                                                    'location_id': picking_type.default_location_src_id.id,
                                                                    'location_dest_id': picking_type.default_location_dest_id.id,
                                                                    'origin': production.name})
                    move_list.write({'picking_id': picking.id})
                    picking.recheck_availability()
                    # picking.get_account_move_lines()  # din localizare
            #for move in production.move_raw_ids:
                #if not move.quantity_done_store:
                    #move.quantity_done_store = move.product_qty

            # nota de predare
            move_list = self.env['stock.move']
            picking = False
            for move in production.move_finished_ids:
                if not move.picking_id:
                    move_list += move
                else:
                    picking = move.picking_id
            if move_list:
                picking_type = self.env.ref('stock.picking_type_receipt_production', raise_if_not_found=True)

                if picking_type:
                    if not picking:
                        picking = self.env['stock.picking'].create({'picking_type_id': picking_type.id,
                                                                    'date': production.date_planned_start,
                                                                    'location_id': picking_type.default_location_src_id.id,
                                                                    'location_dest_id': picking_type.default_location_dest_id.id,
                                                                    'origin': production.name})
                    move_list.write({'picking_id': picking.id})
                    picking.recheck_availability()
        return

    @api.multi
    def action_see_picking(self):
        pickings = self.env['stock.picking']
        for move in self.move_raw_ids:
            pickings |= move.picking_id
        for move in self.move_finished_ids:
            pickings |= move.picking_id

        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        if pickings:
            action['domain'] = "[('id','in'," + str(pickings.ids) + " )]"
        return action


    """
    @api.multi
    def post_inventory(self):
        super(MrpProduction,self).post_inventory()
        for order in self:
            if order.move_raw_ids:
                picking = order.move_raw_ids[0].picking_id
                for op in picking.pack_operation_ids:
                    if not op.qty_done:
                        op.qty_done = op.product_qty

    """
