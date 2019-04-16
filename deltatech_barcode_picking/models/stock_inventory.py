# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, api, models, _


class Inventory(models.Model):
    _name = "stock.inventory"
    _inherit = ["stock.inventory", 'barcodes.barcode_events_mixin']

    def _add_product(self, product, qty=1.0):
        line = self.line_ids.filtered(lambda r: r.product_id.id == product.id)
        if line:
            line.product_qty += qty
            if 'is_ok' in line._fields:  # campul se gaseste in deltatech_inventory
                line.is_ok = True
            message = _('The %s product quantity was set to %s') % (product.name, line.product_qty)
            self.env.user.notify_info(message=message)
        else:
            vals = {
                'product_id': product.id,
                'date_planned': fields.Datetime.now(),
                'product_uom': product.uom_po_id.id,
                'product_qty': 1,
                'location_id': self.location_id.id,
                'company_id': self.company_id.id,
                'is_ok': True
            }
            line = self.line_ids.new(vals)
            line._compute_theoretical_qty()
            self.line_ids += line
            message = _('The %s product was added') % (product.name)
            self.env.user.notify_info(message=message)



    def on_barcode_scanned(self, barcode):
        if self.state not in ['confirm']:
            self.env.user.notify_danger(message=_('Status does not allow scanning'))
            return
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if product:
            self._add_product(product)
        else:
            self.env.user.notify_danger(message=_('There is no product with barcode %s') % barcode )