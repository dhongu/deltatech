# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging
import threading

from odoo import api, fields, models, tools, registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import odoo.addons.decimal_precision as dp
from odoo.osv import expression
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class ProcurementComputeProducts(models.TransientModel):
    _name = 'procurement.compute.products'
    _description = 'Compute schedulers'

    item_ids = fields.One2many('procurement.compute.products.item', 'compute_id')
    group_id = fields.Many2one('procurement.group', string="Procurement Group")
    background = fields.Boolean('Run in background', default=False)
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", )

    make_prod = fields.Boolean(string='Make production order', default=True)
    make_purch = fields.Boolean(string="Make purchase order", default=False)

    # with_reservation = fields.Boolean(default=True)
    # stock_min_max = fields.Boolean()

    @api.model
    def default_get(self, fields):
        defaults = super(ProcurementComputeProducts, self).default_get(fields)
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', False)

        warehouse = self.env.user.company_id.warehouse_id

        qty = {}
        qty_reserved = {}
        products = self.env['product.product']
        if active_model == 'product.template':
            product_tmpl = self.env['product.template'].browse(active_ids)
            for tmpl in product_tmpl:
                products |= tmpl.product_variant_ids

        if active_model == 'product.product':
            products = self.env['product.product'].browse(active_ids)

        for product in products:
            qty[product.id] = -1.0 * product.virtual_available

        # nu trebuie combinate comenzi din companii diferite
        if active_model == 'mrp.production':
            productions = self.env['mrp.production'].browse(active_ids)
            for production in productions:
                defaults['group_id'] = production.procurement_group_id.id
                for move in production.move_raw_ids:
                    products |= move.product_id
                    if move.state == 'draft':
                        product_qty = move.product_uom._compute_quantity(move.product_uom_qty, move.product_id.uom_id)
                    else:
                        product_qty = move.product_qty

                    if move.product_id.id in qty:
                        qty[move.product_id.id] += product_qty
                    else:
                        qty[move.product_id.id] = product_qty

                    if move.state != 'draft':  # daca miscarea are o rezervare
                        if move.product_id.id in qty_reserved:
                            qty_reserved[move.product_id.id] += move.reserved_availability
                        else:
                            qty_reserved[move.product_id.id] = move.reserved_availability

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
            # purcahse_orders = self.env['purchase.order'].search([('group_id', '=', defaults['group_id']),
            #                                                      ('state', 'in', ['draft', 'sent'])])
            polines = self.env['purchase.order.line'].search([
                ('state', 'in', ('draft', 'sent', 'to approve')),
                ('order_id.group_id', '=', defaults['group_id']),
                ('product_id', 'in', products.ids)
            ])
            for poline in polines:
                qty[poline.product_id.id] -= poline.product_uom._compute_quantity(poline.product_qty,
                                                                                  poline.product_id.uom_id,
                                                                                  round=False)
            productions = self.env['mrp.production'].search([
                ('state', 'in', ('confirmed', 'planned', 'progress')),
                ('procurement_group_id', '=', defaults['group_id']),
                ('product_id', 'in', products.ids)
            ])
            for production in productions:
                qty[production.product_id.id] -= (production.product_qty - production.qty_produced)
        else:
            purcahse_orders = self.env['purchase.order'].search([('state', 'in', ['draft', 'sent'])])
            # se scazut ce este deja in comenzi de achzitii ciorna
            for order in purcahse_orders:
                for line in order.order_line:
                    if line.product_id.id in qty:
                        qty[line.product_id.id] -= line.product_qty


        for product in products:
            product = product.with_context({'location': location.ids})
            if product.id in  qty_reserved:
                qty_available = qty_reserved[product.id]
            else:
                qty_available = product.qty_available

            virtual_available = qty_available + product.incoming_qty
            qty[product.id] -= virtual_available

            #if virtual_available < 0.0:
            #todo: se verificat daca cantitatea care este dispobibila (sau in comanda de achiztie) este pentru aceasta comanda
            # if 'group_id' in defaults:
            #     qty[product.id] = min([-1 * product.virtual_available, qty[product.id]])
            # else:
            #     qty[product.id] = -1 * product.virtual_available

        defaults['warehouse_id'] = warehouse.id
        defaults['item_ids'] = []
        for product in products:

            if float_compare(qty[product.id], 0, precision_rounding=product.uom_id.rounding) > 0:
                defaults['item_ids'].append((0, 0, {'product_id': product.id,
                                                    'qty': qty[product.id],
                                                    'uom_id': product.uom_id.id}))

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

            scheduler_cron = self.sudo().env.ref('stock.ir_cron_scheduler_action')
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

                ProcurementGroup = self.env['procurement.group']
                ProcurementGroup.with_context(product_ids=products.ids).run_scheduler(use_new_cursor=self._cr.dbname,
                                                                                      company_id=self.env.user.company_id)

            self._cr.close()
            return {}

    @api.multi
    def individual_procurement(self):
        self.ensure_one()
        ProcurementGroup = self.env['procurement.group'].with_context(mail_notrack=True)
        productions = self.env['mrp.production']
        location = self.warehouse_id.lot_stock_id
        rule_domain = [('location_id', '=', location.id)]
        OrderPoint = self.env['stock.warehouse.orderpoint']
        group_name = self.group_id.name
        for item in self.item_ids:
            if item.qty > 0:
                values = {
                    'date_planned': fields.Date.today(),
                    'warehouse_id': self.warehouse_id,
                    'group_id': self.group_id
                }

                rule = ProcurementGroup._get_rule(item.product_id, self.warehouse_id.lot_stock_id, values)

                if not rule:
                    continue

                if rule.action == 'buy':
                    if rule.group_propagation_option != 'propagate':
                        rule.write({'group_propagation_option':'propagate'})
                    if not self.make_purch:
                        continue
                elif rule.action == 'manufacture':
                    if not self.make_prod:
                        continue
                else:
                    continue

                # procurement = self.env["procurement.order"].search([('group_id', '=', self.group_id.id)],
                #                                                    limit=1, order='date_planned')
                # date_planned = procurement.date_planned or fields.Date.today()
                origin = self.group_id.name or '/'
                qty = item.qty + item.qty * item.product_id.scrap  # se adauga si pierderea
                # qty = item.product_id.uom_id._compute_quantity(qty, item.product_id.uom_id)  # rotunjire cantitate de aprovizionat
                # if item.product_id.scrap:
                #     msg = ('Necesar %s + scrap %s = %s.') % (item.qty, item.qty * item.product_id.scrap, qty)
                # else:
                #     msg = ('Necesar %s ') % (qty)


                orderpoint = item.orderpoint_id

                name = 'SUP: %s ' % (origin)
                name = name + orderpoint.name
                qty += max(orderpoint.product_min_qty, orderpoint.product_max_qty)
                remainder = orderpoint.qty_multiple > 0 and qty % orderpoint.qty_multiple or 0.0

                if float_compare(remainder, 0.0, precision_rounding=orderpoint.product_uom.rounding) > 0:
                    qty += orderpoint.qty_multiple - remainder

                if float_compare(qty, 0.0, precision_rounding=orderpoint.product_uom.rounding) < 0:
                    continue

                qty = float_round(qty, precision_rounding=orderpoint.product_uom.rounding)
                #_logger.info('Rulare aprovizionare pt %s' % item.product_id.name)
                ProcurementGroup.run(item.product_id, qty, item.uom_id, location, name, group_name, values)
            # cum determin ce comenzi  de productie au fost facute ?
            # if new_procurement.production_id:
            #     productions |= new_procurement.production_id

        active_model = self.env.context.get('active_model', False)

        if productions and active_model == 'mrp.production':
            new_context = {'active_ids': productions.ids, 'active_model': 'mrp.production'}
            new_wizard = self.with_context(new_context).create({'background': self.background,
                                                                'make_prod': self.make_prod,
                                                                'make_purch': self.make_purch,
                                                                'group_id': self.group_id.id})
            new_wizard.individual_procurement()

    @api.multi
    def procure_calculation(self):
        # verific faca toate produsele au punct re reaprovizionare

        OrderPoint = self.env['stock.warehouse.orderpoint']

        products = self.env['product.product']
        for item in self.item_ids:
            order_point = OrderPoint.search([('product_id', '=', item.product_id.id)], limit=1)
            if not order_point:
                order_point = OrderPoint.create(
                    {'product_id': item.product_id.id, 'product_min_qty': 0.0, 'product_max_qty': 0.0})
            item.write({'orderpoint_id': order_point.id})
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
    uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure')
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint')
