# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, api, models


class Picking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    def _add_product(self, product, qty=1.0):
        line = self.move_lines.filtered(lambda r: r.product_id.id == product.id)
        if line:
            # if self.state == 'draft':
            #     line.product_uom_qty += qty
            #     line.ordered_qty += qty

            line.quantity_done += qty
        else:
            if self.state == 'draft':
                vals = {
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    # 'product_uom_qty':1,
                    # 'ordered_qty':1,
                    'quantity_done': 1,
                    'date_expected': fields.Datetime.now(),
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'state': 'draft',
                }
                line = self.move_lines.new(vals)
                line.onchange_product_id()
                self.move_lines += line

    def on_barcode_scanned(self, barcode):
        if self.state not in ['draft', 'assigned']:
            return
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if product:
            self._add_product(product)
