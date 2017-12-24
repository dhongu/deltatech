# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import threading

from odoo import api, fields, models, tools, registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import odoo.addons.decimal_precision as dp
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class ProcurementComputeProducts(models.TransientModel):
    _name = 'procurement.compute.products'
    _description = 'Compute schedulers'

    item_ids = fields.One2many('procurement.compute.products.item', 'compute_id')
    group_id = fields.Many2one('procurement.group', string="Procurement Group")
    background = fields.Boolean('Run in background', default=True)
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")

    make_prod = fields.Boolean(string = 'Make production order', default=True)
    make_purch = fields.Boolean(string= "Make purchase order", default=False)
    # stock_min_max = fields.Boolean()

    @api.model
    def default_get(self, fields):
        defaults = super(ProcurementComputeProducts, self).default_get(fields)
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)

        warehouse = self.env.user.company_id.warehouse_id
        #warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)


        qty = {}
        products = self.env['product.product']
        if active_model == 'product.template':
            product_tmpl = self.env['product.template'].browse(active_ids)
            for tmpl in product_tmpl:
                products |= tmpl.product_variant_ids

        if active_model == 'product.product':
            products = self.env['product.product'].browse(active_ids)

        for product in products:
            qty[product.id] = -1.0 * product.virtual_available

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
        if 'group_id' in defaults:

            procurements = self.env["procurement.order"].search([('product_id', 'in', products.ids),
                                                                 ('state', 'in', ['exception', 'running']),
                                                                 ('group_id', '=', defaults['group_id']),
                                                                 ('location_id', '=', location.id)])
            procurements.run()
            for procurement in procurements:
                qty[procurement.product_id.id] = qty[procurement.product_id.id] - procurement.product_qty

        for product in products:
            product = product.with_context({'location': location.ids})
            if 'group_id' in defaults:
                qty[product.id] = min([-1 * product.virtual_available, qty[product.id]])
            else:
                qty[product.id] = -1 * product.virtual_available

        defaults['warehouse_id'] = warehouse.id
        defaults['item_ids'] = []
        for product in products:
            if qty[product.id] > 0:
                defaults['item_ids'].append((0, 0, {'product_id': product.id, 'qty': qty[product.id]}))

        return defaults

    @api.onchange('group_id')
    def onchange_group_id(self):
        if not self.group_id:
            self.background = True

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

            if self.group_id:
                self.individual_procurement()
                self._cr.commit()
            else:
                products = self.env['product.product']
                for item in self.item_ids:
                    products |= item.product_id
                Procurement = self.env['procurement.order']
                for company in self.env.user.company_ids:
                    Procurement.supply(products, use_new_cursor=self._cr.dbname, company_id=company.id)
            # close the new cursor
            """
            self.env['procurement.order']._procure_orderpoint_confirm(
                use_new_cursor=new_cr.dbname,
                company_id=self.env.user.company_id.id)
            """
            self._cr.close()
            return {}

    @api.multi
    def individual_procurement(self):
        self.ensure_one()

        productions = self.env['mrp.production']
        location = self.warehouse_id.lot_stock_id
        rule_domain = [('location_id','=',location.id)]
        OrderPoint = self.env['stock.warehouse.orderpoint']
        for item in self.item_ids:
            if item.qty > 0:
                product_routes = item.product_id.route_ids | item.product_id.categ_id.total_route_ids

                rule = self.env['procurement.rule'].search(expression.AND([[('route_id', 'in', product_routes.ids)], rule_domain]),
                                  order='route_sequence, sequence', limit=1)
                if not rule:
                    continue

                if rule.action == 'buy':
                    if not self.make_purch:
                        continue
                elif rule.action == 'manufacture':
                    if not self.make_prod:
                        continue
                else:
                    continue

                procurement = self.env["procurement.order"].search([('group_id', '=', self.group_id.id)],
                                                                   limit=1, order='date_planned')
                date_planned = procurement.date_planned or fields.Date.today()
                origin = procurement.origin
                qty = item.qty + item.qty * item.product_id.scrap  # se adauga si pierderea
                orderpoint = OrderPoint.search([('product_id', '=', item.product_id.id),
                                                ('location_id', '=', location.id)])
                if item.product_id.scrap:
                    msg = ('Necesar %s + scrap %s = %s.') % (item.qty, item.qty * item.product_id.scrap, qty)
                else:
                    msg =  ('Necesar %s ') % (qty)
                name = 'SUP: %s ' % (procurement.origin)
                if orderpoint:
                    name = name + orderpoint.name
                    qty += max(orderpoint.product_min_qty, orderpoint.product_max_qty)
                    remainder = orderpoint.qty_multiple > 0 and qty % orderpoint.qty_multiple or 0.0

                    if float_compare(remainder, 0.0, precision_rounding=orderpoint.product_uom.rounding) > 0:
                        qty += orderpoint.qty_multiple - remainder

                    if float_compare(qty, 0.0, precision_rounding=orderpoint.product_uom.rounding) < 0:
                        continue

                    qty = float_round(qty, precision_rounding=orderpoint.product_uom.rounding)

                    date_planned = orderpoint._get_date_planned(fields.Date.from_string(date_planned))

                new_procurement = self.env["procurement.order"].create({
                    'name': name,
                    'date_planned': date_planned,
                    'product_id': item.product_id.id,
                    'product_qty': qty,
                    'product_uom': item.product_id.uom_id.id,
                    'warehouse_id': self.warehouse_id.id,
                    'location_id': location.id,
                    'origin': origin,
                    'group_id': self.group_id.id,
                    'company_id': self.warehouse_id.company_id.id})
                new_procurement.run()
                new_procurement.message_post(body=msg)
            if new_procurement.production_id:
                productions |= new_procurement.production_id

        active_model = self.env.context.get('active_model', False)



        if productions and active_model == 'mrp.production':
            new_context = {'active_ids': productions.ids, 'active_model': 'mrp.production'}
            new_wizard = self.with_context(new_context).create({'background': self.background,
                                                                'make_prod':self.make_prod,
                                                                'make_purch':self.make_purch,
                                                                'group_id': self.group_id.id})
            new_wizard.individual_procurement()

    @api.multi
    def procure_calculation(self):
        if self.group_id and not self.background:
            self.individual_procurement()

        else:
            threaded_calculation = threading.Thread(target=self._procure_calculation_products, args=())
            threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}


class ProcurementComputeProductsItem(models.TransientModel):
    _name = 'procurement.compute.products.item'
    _description = 'Compute schedulers Item'

    compute_id = fields.Many2one('procurement.compute.products')
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
