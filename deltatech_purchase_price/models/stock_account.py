# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models
from collections import defaultdict
from odoo.tools import float_compare, float_round, float_is_zero, pycompat


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _get_price_unit(self):
        """ Returns the unit price to store on the quant """
        if self.purchase_line_id:
            get_param = self.env['ir.config_parameter'].sudo().get_param
            update_product_price = get_param('purchase.update_product_price', default=True)
            if update_product_price == 'False':
                update_product_price = False

            update_product_standard_price = get_param('purchase.update_product_standard_price', default=False)
            if update_product_standard_price == 'False':
                update_product_standard_price = False

            price_unit = self.purchase_line_id.with_context(date=self.date)._get_stock_move_price_unit()
            if update_product_standard_price:
                self.product_id.product_tmpl_id.write({'standard_price': price_unit})

            self.write({'price_unit': price_unit}) #mai trebuie sa pun o conditie de status ?
            # update price form last receipt
            for seller in self.product_id.seller_ids:
                if seller.name == self.purchase_line_id.order_id.partner_id:
                    if seller.min_qty == 0.0 and seller.date_start is False and seller.date_end is False:
                        if seller.currency_id:
                            if seller.currency_id == self.purchase_line_id.order_id.currency_id:
                                seller_price_unit = self.purchase_line_id.price_unit
                            else:
                                seller_price_unit = self.env.user.company_id.currency_id.compute(price_unit,
                                                                                                 seller.currency_id)
                        else:
                            seller_price_unit = price_unit
                        if update_product_price:

                            seller.write({'price': seller_price_unit})

                        # if update_product_standard_price:
                        #     if seller.currency_id:
                        #         standard_price = seller.currency_id.compute(seller_price_unit, self.env.user.company_id.currency_id )
                        #     self.product_id.write({'standard_price':standard_price})


            return price_unit

        return super(StockMove, self)._get_price_unit()



    @api.multi
    def product_price_update_before_done(self, forced_qty=None):

        super(StockMove, self.with_context(force_fifo_to_average=True)).product_price_update_before_done(forced_qty)

