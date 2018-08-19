# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductLocationSelect(models.TransientModel):
    _name = 'product.location.select'
    _description = "Product Location Select"

    location_id = fields.Many2one('stock.location', string='Location')
    sale_order_id = fields.Many2one('sale.order')
    picking_id = fields.Many2one('stock.picking')

    @api.model
    def default_get(self, fields_list):
        defaults = super(ProductLocationSelect, self).default_get(fields_list)
        location = False
        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if active_model == 'sale.order':
            sale_order = self.env[active_model].browse(active_id)
            defaults['sale_order_id'] = sale_order.id
            warehouse = sale_order.warehouse_id
            location = warehouse.lot_stock_id
            if sale_order.state not in ['draft']:
                raise UserError(_('Sale order state not allow to add products'))
        if active_model == 'stock.picking':
            picking = self.env[active_model].browse(active_id)
            defaults['picking_id'] = picking.id
            location = picking.location_id
            if picking.state not in ['draft', 'assigned']:
                raise UserError(_('Picking state not allow to add products'))
        if location:
            defaults['location_id'] = location.id
        return defaults

    @api.multi
    def do_select(self):

        vals = []
        Product = self.env['product.product']
        # Empty recordset of products available in stock_quants
        quant_products = self.env['product.product']
        # Empty recordset of products to filter
        products_to_filter = self.env['product.product']

        self.env.cr.execute("""SELECT product_id, sum(quantity) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
                    FROM stock_quant
                    WHERE location_id = %s
                    GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % self.location_id.id)
        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            # for void_field in [item[0] for item in product_data.items() if item[1] is None]:
            #     product_data[void_field] = False
            # product_data['theoretical_qty'] = product_data['product_qty']
            # if product_data['product_id']:
            #     product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
            #     quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)

        for val in vals:
            if val['product_qty'] < 0:
                continue
            if self.picking_id:
                line_data = {
                    'picking_id': self.picking_id.id,
                    'product_id': val['product_id'],
                    'quantity_done': val['product_qty'],
                    'location_id': self.picking_id.location_id.id,
                    'location_dest_id': self.picking_id.location_dest_id.id,
                }

                line = self.env['stock.move'].new(line_data)
                line.onchange_product_id()
                new_vals = {k: v or False for k, v in dict(line._cache).items()}
                line_data = line._convert_to_write(new_vals)
                self.env['stock.move'].create(line_data)

            if self.sale_order_id:
                order_line_data = {
                    'product_id': val['product_id'],
                    # 'product_uom': val['product_uom_id'],
                    'product_uom_qty': val['product_qty'],
                    'state': 'draft',
                    'order_id': self.sale_order_id.id,
                }
                order_line = self.env['sale.order.line'].new(order_line_data)
                order_line.product_id_change()
                order_line.product_uom_change()

                new_vals = {k: v or False for k, v in dict(order_line._cache).items()}
                line_data = order_line._convert_to_write(new_vals)
                self.env['sale.order.line'].create(line_data)
