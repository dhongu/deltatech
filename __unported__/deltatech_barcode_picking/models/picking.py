# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, api, models, _


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    product_barcode_scanner = fields.Boolean('Allowed to add products by scanning', default=True)



class Picking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']



    def _add_product(self, product, qty=1.0):


        line = self.move_ids_without_package.filtered(lambda r: r.product_id.id == product.id)
        if line.show_details_visible:
            message = _('For %s it is necessary to specify some details.') % (product.name)
            self.env.user.notify_warning(message=message)
            line.is_quantity_done_editable = True


        if line:
            if line.reserved_availability >= line.quantity_done+qty:
                line.quantity_done += qty
                message = _('The %s product quantity was set to %s') % (product.name, line.quantity_done)
                self.env.user.notify_info(message=message)
            else:
                self.env.user.notify_warning(message=_('Your reserved quantity has already been reached'))
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

            else:
                message = _('%s product does not exist in this list') %  product.name
                self.env.user.notify_danger(message=message)




    def on_barcode_scanned(self, barcode):
        if self.state not in ['draft', 'assigned']:
            self.env.user.notify_danger(message=_('Status does not allow scanning') )
            return
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if product:
            self._add_product(product)
        else:
            self.env.user.notify_danger(message=_('There is no product with barcode %s') % barcode )




