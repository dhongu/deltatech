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

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        if self.product_id.qty_multiple and self.product_id.qty_multiple != 1:
            qty = self.product_uom_qty
            qty_multiple = self.product_id.qty_multiple
            remainder = self.product_uom_qty % qty_multiple

            if float_compare(remainder, 0.0, precision_rounding=self.product_uom.rounding) > 0:
                qty += qty_multiple - remainder

            if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) > 0:
                qty = float_round(qty, precision_rounding=self.product_uom.rounding)
                self.product_uom_qty = qty

        super(SaleOrderLine, self)._onchange_product_uom_qty()

