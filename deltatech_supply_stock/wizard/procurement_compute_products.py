# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import threading

from odoo import api, fields, models, tools, registry

_logger = logging.getLogger(__name__)


class ProcurementComputeProducts(models.TransientModel):
    _name = 'procurement.compute.products'
    _description = 'Compute schedulers'

    item_ids = fields.One2many('procurement.compute.products.item', 'compute_id')

    group_id = fields.Many2one('procurement.group', string="Procurement Group")

    @api.model
    def default_get(self, fields):
        defaults = super(ProcurementComputeProducts, self).default_get(fields)
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)

        qty = {}
        products = self.env['product.product']
        if active_model == 'product.template':
            product_tmpl = self.env['product.template'].browse(active_ids)
            for tmpl in product_tmpl:
                products |= tmpl.product_variant_ids

        if active_model == 'product.product':
            products = self.env['product.product'].browse(active_ids)

        for product in products:
            qty[product.id] = -1 * product.virtual_available

        if active_model == 'mrp.production':
            productions = self.env['mrp.production'].browse(active_ids)
            for production in productions:
                for move in production.move_raw_ids:
                    products |= move.product_id
                    if move.product_id.id in qty:
                        qty[move.product_id.id] += move.product_uom_qty
                    else:
                        qty[move.product_id.id] = move.product_uom_qty

        if active_model == 'sale.order':
            sale_orders = self.env['sale.order'].browse(active_ids)
            for sale_order in sale_orders:
                defaults['group_id'] = sale_order.procurement_group_id.id
                for line in sale_order.order_line:
                    products |= line.product_id
                    if line.product_id.id in qty:
                        qty[line.product_id.id] += line.product_uom_qty
                    else:
                        qty[line.product_id.id] = line.product_uom_qty

        for product in products:
            qty[product.id] = min([-1 * product.virtual_available, qty[product.id]])

        defaults['item_ids'] = []
        for product in products:
            defaults['item_ids'].append((0, 0, {'product_id': product.id, 'qty': qty[product.id]}))


        return defaults

    @api.multi
    def _procure_calculation_products(self):
        with api.Environment.manage():
            # As this function is in a new thread, i need to open a new cursor, because the old one may be closed
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))  # TDE FIXME
            scheduler_cron = self.sudo().env.ref('procurement.ir_cron_scheduler_action')
            # Avoid to run the scheduler multiple times in the same time
            try:
                with tools.mute_logger('odoo.sql_db'):
                    self._cr.execute("SELECT id FROM ir_cron WHERE id = %s FOR UPDATE NOWAIT", (scheduler_cron.id,))
            except Exception:
                _logger.info('Attempt to run procurement scheduler aborted, as already running')
                self._cr.rollback()
                self._cr.close()
                return {}
            products = self.env['product.product']
            for item in self.item_ids:
                products |= item.product_id
            Procurement = self.env['procurement.order']
            for company in self.env.user.company_ids:
                Procurement.supply(products, use_new_cursor=self._cr.dbname, company_id=company.id)
            # close the new cursor
            self._cr.close()
            return {}

    @api.multi
    def procure_calculation(self):
        if self.group_id:
            warehouse = self.env['stock.warehouse'].search([], limit=1)
            location = warehouse.lot_stock_id

            for item in self.item_ids:
                move = self.env['stock.move'].search([('product_id', '=', item.product_id.id),
                                                      ('group_id', '=', self.group_id.id),
                                                      ('state', 'in', ['waiting', 'confirmed']),
                                                      ('location_id', '=', location.id)],
                                                     limit=1,
                                                     order='date_expected')
                date_planned = move.date_expected

                procurement = self.env["procurement.order"].create({
                    'name': 'SUP: %s' % (self.env.user.login),
                    'date_planned': date_planned,
                    'product_id': item.product_id.id,
                    'product_qty': item.qty,
                    'product_uom': item.product_id.uom_id.id,
                    'warehouse_id': warehouse.id,
                    'location_id': location.id,
                    'group_id': move.group_id.id,
                    'company_id': warehouse.company_id.id})
                procurement.run()
        else:
            threaded_calculation = threading.Thread(target=self._procure_calculation_products, args=())
            threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}


class ProcurementComputeProductsItem(models.TransientModel):
    _name = 'procurement.compute.products.item'
    _description = 'Compute schedulers Item'

    compute_id = fields.Many2one('procurement.compute.products')
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string='Quantity')
