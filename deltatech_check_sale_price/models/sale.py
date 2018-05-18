# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'



    @api.onchange('price_unit','product_uom')
    def onchange_price_unit(self):
        if self.product_id:
            highest_price = 0.0
            to_currency = self.order_id.pricelist_id.currency_id or  self.env.user.company_id.currency_id
            for seller in self.product_id.seller_ids:
                from_currency = seller.currency_id or self.env.user.company_id.currency_id

                seller_price_unit = from_currency.compute(seller.price, to_currency)

                highest_price = max(highest_price, seller_price_unit)

            highest_price = self.product_id.uom_po_id._compute_price(highest_price, self.product_uom)

            if highest_price and self.price_unit and highest_price > self.price_unit:
                self.price_unit = highest_price
                return {
                    'warning': {'title': "Warning",
                                'message': _('It is not allowed to sell below the price %s') % str(highest_price)},
                }
