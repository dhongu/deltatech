# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.exceptions import UserError, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def fix_qty_multiple(self, product, product_uom, qty):
        if product.qty_multiple and product.qty_multiple != 1:
            qty_multiple = product.qty_multiple
            remainder = qty % qty_multiple

            if float_compare(remainder, 0.0, precision_rounding=product_uom.rounding) > 0:
                qty += qty_multiple - remainder

            if float_compare(qty, 0.0, precision_rounding=product_uom.rounding) > 0:
                qty = float_round(qty, precision_rounding=product_uom.rounding)

        return qty

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        self.product_uom_qty = self.fix_qty_multiple(self.product_id, self.product_uom, self.product_uom_qty)
        super(SaleOrderLine, self)._onchange_product_uom_qty()

    @api.multi
    def write(self, vals):
        if len(self) == 1 and 'product_uom_qty' in vals:
            if 'product_id' in vals:
                product = self.env['product.product'].browse(vals['product_id'])
            else:
                product = self.product_id
            if 'product_uom' in vals:
                product_uom = self.env['uom.uom'].browse(vals['product_uom'])
            else:
                product_uom = self.product_uom
            vals['product_uom_qty'] = self.fix_qty_multiple(product, product_uom, vals['product_uom_qty'])

        super(SaleOrderLine, self).write(vals)
