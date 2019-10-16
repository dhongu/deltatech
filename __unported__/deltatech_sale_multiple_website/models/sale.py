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


# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#     @api.multi
#     def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
#
#         self.ensure_one()
#         product_context = dict(self.env.context)
#         product = self.env['product.product'].with_context(product_context).browse(int(product_id))
#
#         try:
#             if add_qty:
#                 add_qty = float(add_qty)
#         except ValueError:
#             add_qty = 1
#         try:
#             if set_qty:
#                 set_qty = float(set_qty)
#         except ValueError:
#             set_qty = 0
#
#         if product.qty_multiple and product.qty_multiple != 1:
#
#
#             qty = add_qty or set_qty
#             qty_multiple = product.qty_multiple
#             remainder = qty % qty_multiple
#
#             if float_compare(remainder, 0.0, precision_rounding=self.product_uom.rounding) > 0:
#                 qty += qty_multiple - remainder
#
#             if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) > 0:
#                 qty = float_round(qty, precision_rounding=self.product_uom.rounding)
#                 self.product_uom_qty = qty
#
#         res = super(SaleOrder, self)._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty,
#                                                   set_qty=set_qty, **kwargs)
#         return res

