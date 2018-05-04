# -*- coding: utf-8 -*-
# ©  2015-2017 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import odoo.addons.decimal_precision as dp

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import math






class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_id = fields.Many2one('product.product',required=False)

    product_tmpl_id = fields.Many2one('product.template',
                                      domain=[('type', 'in', ['product', 'consu'])],
                                      readonly=True, required=True,
                                      states={'confirmed': [('readonly', False)]}, related=False)

    @api.onchange('product_id', 'picking_type_id', 'company_id')
    def onchange_product_id(self):
        self.product_tmpl_id = self.product_id.product_tmpl_id
        return super(MrpProduction, self).onchange_product_id()

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            if self.product_tmpl_id.product_variant_count == 1:
                self.product_id = self.product_tmpl_id.product_variant_id
            else:
                bom = self.env['mrp.bom']._bom_find(product_tmpl=self.product_tmpl_id,
                                                    picking_type=self.picking_type_id,
                                                    company_id=self.company_id.id)
                if bom.type == 'normal':
                    self.bom_id = bom.id
                else:
                    self.bom_id = False
                self.product_uom_id = self.product_tmpl_id.uom_id.id
                return {'domain': {'product_uom_id': [('category_id', '=', self.product_tmpl_id.uom_id.category_id.id)]}}



    def _generate_finished_moves(self):
        if self.product_id:
            return super(MrpProduction, self)._generate_finished_moves()

        qty_inc = int(self.product_qty / self.product_tmpl_id.product_variant_count)
        product_qty = qty_inc + self.product_qty - qty_inc*self.product_tmpl_id.product_variant_count
        for product_id in  self.product_tmpl_id.product_variant_ids:

            move = self.env['stock.move'].create({
                'name': self.name,
                'date': self.date_planned_start,
                'date_expected': self.date_planned_start,
                'product_id': product_id.id,
                'product_uom': self.product_uom_id.id,
                'product_uom_qty': product_qty,
                'location_id': product_id.property_stock_production.id,
                'location_dest_id': self.location_dest_id.id,
                'company_id': self.company_id.id,
                'production_id': self.id,
                'origin': self.name,
                'group_id': self.procurement_group_id.id,
                'unit_factor': 1 / self.product_tmpl_id.product_variant_count,
                'propagate': self.propagate,
                'move_dest_ids': [(4, x.id) for x in self.move_dest_ids],
            })
            product_qty = qty_inc
            move._action_confirm()
        return move

    @api.multi
    @api.depends('workorder_ids.state', 'move_finished_ids', 'is_locked')
    def _get_produced_qty(self):
        for production in self:
            done_moves = production.move_finished_ids.filtered(
                lambda x: x.state != 'cancel' and x.product_id.product_tmpl_id.id == production.product_tmpl_id.id)
            qty_produced = sum(done_moves.mapped('quantity_done'))
            wo_done = True
            if any([x.state not in ('done', 'cancel') for x in production.workorder_ids]):
                wo_done = False
            production.check_to_done = production.is_locked and done_moves and (
                        qty_produced >= production.product_qty) and (
                                                   production.state not in ('done', 'cancel')) and wo_done
            production.qty_produced = qty_produced
        return True


    #metoda standard a fost inlocuita doar pentru a putea prelua locatia de la product_tmpl_id
    def _generate_raw_move(self, bom_line, line_data):
        quantity = line_data['qty']
        # alt_op needed for the case when you explode phantom bom and all the lines will be consumed in the operation given by the parent bom line
        alt_op = line_data['parent_line'] and line_data['parent_line'].operation_id.id or False
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return self.env['stock.move']
        if bom_line.product_id.type not in ['product', 'consu']:
            return self.env['stock.move']
        if self.routing_id:
            routing = self.routing_id
        else:
            routing = self.bom_id.routing_id
        if routing and routing.location_id:
            source_location = routing.location_id
        else:
            source_location = self.location_src_id
        original_quantity = (self.product_qty - self.qty_produced) or 1.0
        data = {
            'sequence': bom_line.sequence,
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'bom_line_id': bom_line.id,
            'product_id': bom_line.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': bom_line.product_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_tmpl_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': bom_line.operation_id.id or alt_op,
            'price_unit': bom_line.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'warehouse_id': source_location.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'unit_factor': quantity / original_quantity,
        }
        return self.env['stock.move'].create(data)