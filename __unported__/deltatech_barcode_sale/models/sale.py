# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, api, models



class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'barcodes.barcode_events_mixin']

    def _add_product(self, product, qty=1.0):
        order_line = self.order_line.filtered(lambda r: r.product_id.id == product.id)
        if order_line:
            order_line.product_uom_qty += qty
            order_line.product_uom_change()
        else:
            vals = {
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': 1,
                'state': 'draft',
                'order_id':self.id,
            }
            order_line = self.order_line.new(vals)
            order_line.product_id_change()
            order_line.product_uom_change()
            #self.order_line += order_line


    def on_barcode_scanned(self, barcode):
        if self.state != 'draft':
            return
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if product:
            self._add_product(product)