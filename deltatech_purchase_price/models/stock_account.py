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
    def get_price_unit(self):
        """ Returns the unit price to store on the quant """
        if self.purchase_line_id:

            price_unit = self.purchase_line_id.with_context(date=self.date)._get_stock_move_price_unit()
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
                                                                                                 seller.currency)
                        else:
                            seller_price_unit = price_unit
                        seller.write({'price': seller_price_unit}) #todo: de facut update doar daca exista o bifa in configurare

            return price_unit

        return super(StockMove, self).get_price_unit()


    @api.multi
    def product_price_update_before_done(self, forced_qty=None):
        super(StockMove, self).product_price_update_before_done()
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'fifo'
        std_price_update = {}
        for move in self.filtered(lambda move: move.location_id.usage in ('supplier') and move.product_id.cost_method == 'fifo'):
            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
            rounding = move.product_id.uom_id.rounding

            if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            else:
                # Get the standard price
                amount_unit = std_price_update.get((move.company_id.id, move.product_id.id)) or move.product_id.standard_price
                qty = forced_qty or move.product_qty
                new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (product_tot_qty_available + move.product_qty)

            tmpl_dict[move.product_id.id] += move.product_qty
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_context(force_company=move.company_id.id).sudo().write({'standard_price': new_std_price})
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price
