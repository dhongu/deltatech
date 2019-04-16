# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, api, models, _



class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'barcodes.barcode_events_mixin']

    def _add_product(self, product, qty=1.0):
        order_line = self.order_line.filtered(lambda r: r.product_id.id == product.id)
        if order_line:
            order_line.product_uom_qty += qty
            order_line.product_uom_change()
            message = _('The %s product quantity was set to %s') % (product.name, order_line.product_uom_qty)
            self.env.user.notify_info(message=message)
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
            message = _('The %s product was added') % ( product.name)
            self.env.user.notify_info(message=message)

    def on_barcode_scanned(self, barcode):
        if self.state != 'draft':
            self.env.user.notify_danger(message=_('Status does not allow scanning'))
            return
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if product:
            self._add_product(product)
        else:
            self.env.user.notify_danger(message=_('There is no product with barcode %s') % barcode )