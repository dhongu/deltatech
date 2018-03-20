# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import threading

from odoo import api, fields, models, tools, registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import odoo.addons.decimal_precision as dp
from odoo.osv import expression
from datetime import datetime

from odoo.tools.misc import split_every


import logging
_logger = logging.getLogger(__name__)



class StockSchedulerWizard(models.TransientModel):
    _name = 'stock.scheduler.wizard'
    _description = 'Compute Schedulers for Selected Orders'

    item_ids = fields.One2many('stock.scheduler.wizard.item', 'wizard_id')
    group_id = fields.Many2one('procurement.group', string="Procurement Group", required=True)
    background = fields.Boolean('Run in background', default=True)
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")

    make_prod = fields.Boolean(string = 'Make production order', default=True)
    make_purch = fields.Boolean(string= "Make purchase order", default=False)

    @api.model
    def default_get(self, fields):
        defaults = super(StockSchedulerWizard, self).default_get(fields)
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)

        warehouse = self.env.user.company_id.warehouse_id

        qty = {}
        products = self.env['product.product']

        # nu trbuie combinate comenzi din companii diferite
        if active_model == 'mrp.production':
            productions = self.env['mrp.production'].browse(active_ids)
            for production in productions:
                defaults['group_id'] = production.procurement_group_id.id
                for move in production.move_raw_ids:
                    products |= move.product_id
                    if move.product_id.id in qty:
                        qty[move.product_id.id] += move.product_qty
                    else:
                        qty[move.product_id.id] = move.product_qty

        if active_model == 'sale.order':
            sale_orders = self.env['sale.order'].browse(active_ids)
            for sale_order in sale_orders:
                defaults['group_id'] = sale_order.procurement_group_id.id
                warehouse = sale_order.warehouse_id

                for line in sale_order.order_line:
                    products |= line.product_id
                    product_qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                    if line.product_id.id in qty:
                        qty[line.product_id.id] += product_qty
                    else:
                        qty[line.product_id.id] = product_qty

        location = warehouse.lot_stock_id

        confirmed_moves = self.env['stock.move'].search([('state', 'in', ['confirmed','partially_available']), ('group_id', '=', defaults['group_id'])])
        # if some products exist for this move, make sure to reserve them
        for move in confirmed_moves:
            move._action_assign()

        # dict to store the already reserved quantities
        # used to substract this quantity from the needed one
        reserved_quantities = {}
        for move in confirmed_moves:
            reserved_quantities[move.product_id.id] = move.reserved_availability

        # dict to store the quantities of products for which there is an existing procurement
        # used to substract this quantity from the needed one
        existing_procurement_quantities = {}
        existing_procurements = self.env['stock.scheduler.existing.procurement'].search([('procurement_group_id', '=', defaults['group_id'])])
        for procurement in existing_procurements:
            existing_procurement_quantities[procurement.product_id.id] = procurement.quantity

        for product in products:
            productId = product.id
            reserved_qty = reserved_quantities.get(productId) or 0.0
            procured_qty = existing_procurement_quantities.get(productId) or 0.0
            qty[productId] = qty[productId] - reserved_qty - procured_qty


        defaults['warehouse_id'] = warehouse.id
        defaults['item_ids'] = []
        for product in products:
            if qty[product.id] > 0:
                defaults['item_ids'].append((0, 0, {'product_id': product.id,
                                                    'qty': qty[product.id],
                                                    'uom_id':product.uom_id.id}))

        return defaults

    @api.multi
    def procure_calculation(self):
        ProcurementGroup = self.env['procurement.group']
        BillOfMaterials = self.env['mrp.bom']
        ExistingProcurement = self.env['stock.scheduler.existing.procurement']
        for item in self.item_ids:
            if item.qty > 0:

                values = {
                'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'warehouse_id': self.warehouse_id,
                'group_id': self.group_id
                }

                rule = ProcurementGroup._get_rule(item.product_id, self.warehouse_id.lot_stock_id, values)

                if not rule:
                    continue

                if rule.action == 'buy':
                    if not self.make_purch:
                        continue
                    else:
                        if not item.product_id.seller_ids:
                            raise Warning('Produsul %s nu are furnizor' % item.product_id.name)

                elif rule.action == 'manufacture':
                    if not self.make_prod:
                        continue
                    else:
                        bom = BillOfMaterials.search(['|', ('product_id', '=', item.product_id.id), ('product_tmpl_id', '=', item.product_id.product_tmpl_id.id)])
                        if not bom:
                            raise Warning('Produsul %s nu are lista de materiale' % item.product_id.name)
                else:
                    continue

                ProcurementGroup.run(item.product_id, item.qty, item.uom_id, self.warehouse_id.lot_stock_id, "", self.group_id.name, values)

                # update the existing procurement table, either by creating a new entry or updating the quantity of an existing entry
                existing_procurements_for_this_product = ExistingProcurement.search([('procurement_group_id', '=', self.group_id.id),('product_id', '=', item.product_id.id)])

                if existing_procurements_for_this_product:
                    existing_procurements_for_this_product.write({'quantity': existing_procurements_for_this_product.quantity + item.qty})
                else:
                    ExistingProcurement.create({
                        'procurement_group_id': self.group_id.id,
                        'product_id': item.product_id.id,
                        'quantity': item.qty,
                        'procurement_type': 'buy' if rule.action == 'buy' else 'manufacture',
                        'location_id': self.warehouse_id.lot_stock_id.id
                    })

        confirmed_moves = self.env['stock.move'].search([('state', '=', 'confirmed'), ('product_uom_qty', '!=', 0.0), ('group_id','=',self.group_id.id)], limit=None, order='priority desc, date_expected asc')
        for moves_chunk in split_every(100, confirmed_moves.ids):
            self.env['stock.move'].browse(moves_chunk)._action_assign()

        return {'type': 'ir.actions.act_window_close'}



class StockSchedulerWizardItem(models.TransientModel):
    _name = 'stock.scheduler.wizard.item'
    _description = 'Compute Schedulers Item'

    wizard_id = fields.Many2one('stock.scheduler.wizard')
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one( 'product.uom', 'Product Unit of Measure' )
