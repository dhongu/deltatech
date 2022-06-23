# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from collections import defaultdict

from odoo import models
from odoo.tools import float_is_zero, safe_eval


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_price_unit(self):
        """Returns the unit price to store on the quant"""
        if self.purchase_line_id:
            get_param = self.env["ir.config_parameter"].sudo().get_param
            update_product_price = get_param("purchase.update_product_price", default="False")
            update_product_price = safe_eval(update_product_price)
            update_list_price = get_param("purchase.update_list_price", default="False")
            update_list_price = safe_eval(update_list_price)

            price_unit = self.purchase_line_id.with_context(date=self.date)._get_stock_move_price_unit()
            self.product_id.write({"last_purchase_price": price_unit})
            self.write({"price_unit": price_unit})  # mai trebuie sa pun o conditie de status ?
            # update price form last receipt

            for seller in self.product_id.seller_ids:
                if seller.name == self.purchase_line_id.order_id.partner_id:
                    if seller.min_qty == 0.0 and seller.date_start is False and seller.date_end is False:
                        if seller.currency_id:
                            if seller.currency_id == self.purchase_line_id.order_id.currency_id:
                                seller_price_unit = self.purchase_line_id.price_unit
                            else:
                                seller_price_unit = self.env.user.company_id.currency_id.compute(
                                    price_unit, seller.currency_id
                                )
                        else:
                            seller_price_unit = price_unit
                        if update_product_price:
                            self.product_id.write({"standard_price": seller_price_unit})
            if update_list_price:
                self.product_id.product_tmpl_id.onchange_last_purchase_price()

            return price_unit

        return super(StockMove, self)._get_price_unit()

    def product_price_update_before_done(self, forced_qty=None):
        super(StockMove, self).product_price_update_before_done(forced_qty)
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        for move in self.filtered(
            lambda move: move._is_in()
            and move.with_context(force_company=move.company_id.id).product_id.cost_method == "fifo"
        ):

            product_tot_qty_available = (
                move.product_id.sudo().with_context(force_company=move.company_id.id).quantity_svl
            )
            product_tot_val = move.product_id.sudo().with_context(force_company=move.company_id.id).value_svl

            rounding = move.product_id.uom_id.rounding

            valued_move_lines = move._get_in_move_lines()
            qty_done = 0
            for valued_move_line in valued_move_lines:
                qty_done += valued_move_line.product_uom_id._compute_quantity(
                    valued_move_line.qty_done, move.product_id.uom_id
                )

            qty = forced_qty or qty_done
            if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            elif float_is_zero(
                product_tot_qty_available + move.product_qty, precision_rounding=rounding
            ) or float_is_zero(product_tot_qty_available + qty, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            else:
                new_std_price = (product_tot_val + (move._get_price_unit() * qty)) / (product_tot_qty_available + qty)

            tmpl_dict[move.product_id.id] += qty_done
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_context(force_company=move.company_id.id).sudo().write(
                {"standard_price": new_std_price}
            )
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # def button_validate(self):
    #     for move in self.move_lines:
    #         if move.product_id.product_tmpl_id.trade_markup:
    #             move.product_id.product_tmpl_id.onchange_last_purchase_price()
    #     return super(StockPicking, self).button_validate()
