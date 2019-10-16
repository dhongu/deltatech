# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, api, models, _



class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'barcodes.barcode_events_mixin']

    def _add_product(self, product, qty=1.0):
        order_line = self.order_line.filtered(lambda r: r.product_id.id == product.id)
        if order_line:
            order_line.product_qty += qty
            message = _('The %s product quantity was set to %s') % (product.name, order_line.product_qty)
            self.env.user.notify_info(message=message)
        else:
            vals = {
                'product_id': product.id,
                # 'name': name,
                'date_planned': fields.Datetime.now(),
                'product_uom': product.uom_po_id.id,
                'product_qty': 1,
                # 'price_unit': product.standard_price,
                'state': 'draft',
            }
            order_line = self.order_line.new(vals)
            order_line.onchange_product_id()
            self.order_line += order_line
            message = _('The %s product was added') % (product.name)
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