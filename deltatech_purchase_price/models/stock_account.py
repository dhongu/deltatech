# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from collections import defaultdict

from odoo import models
from odoo.tools import float_is_zero
from odoo.tools.safe_eval import safe_eval


class StockMove(models.Model):
    _inherit = "stock.move"

    def update_prices(self):
        if self.purchase_line_id and self.product_id == self.purchase_line_id.product_id:
            get_param = self.env["ir.config_parameter"].sudo().get_param
            update_product_price = get_param("purchase.update_product_price", default="False")
            update_product_price = safe_eval(update_product_price)
            update_list_price = get_param("purchase.update_list_price", default="False")
            update_list_price = safe_eval(update_list_price)

            # este neindicat de a se forta actualizarea pretului standard
            update_standard_price = get_param("purchase.update_standard_price", default="False")
            update_standard_price = safe_eval(update_standard_price)

            price_unit = self.purchase_line_id.with_context(date=self.date)._get_stock_move_price_unit()
            self.product_id.write({"last_purchase_price": price_unit})
            self.write({"price_unit": price_unit})  # mai trebuie sa pun o conditie de status ?
            # update price form last receipt
            from_currency = self.env.user.company_id.currency_id
            seller_ids = self.product_id.seller_ids or self.product_id.product_tmpl_id.seller_ids
            for seller in seller_ids:
                if seller.name == self.purchase_line_id.order_id.partner_id.commercial_partner_id:
                    if seller.min_qty == 0.0 and seller.date_start is False and seller.date_end is False:
                        # conversia ar trebui deja sa fie facuta de _get_stock_move_price_unit()
                        to_currency = seller.currency_id or self.env.user.company_id.currency_id
                        seller_price_unit = from_currency.compute(price_unit, to_currency)
                        # seller_price_unit = price_unit
                        if update_product_price:
                            seller.write({"price": seller_price_unit})

            # pretul standard se actualizeaza prin rutinele standard. Aici este o fortare pe ultimul pret
            if update_list_price:
                self.product_id.product_tmpl_id.onchange_last_purchase_price()

            if update_standard_price:
                self.product_id.write({"standard_price": price_unit})

    def product_price_update_before_done(self, forced_qty=None):
        super(StockMove, self).product_price_update_before_done(forced_qty)
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        for move in self.filtered(
            lambda move: move._is_in() and move.with_company(move.company_id).product_id.cost_method == "fifo"
        ):

            product_tot_qty_available = move.product_id.sudo().with_company(move.company_id).quantity_svl
            product_tot_val = move.product_id.sudo().with_company(move.company_id).value_svl

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
            move.update_prices()
            tmpl_dict[move.product_id.id] += qty_done
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            # move.product_id.with_company(move.company_id).sudo().write({"standard_price": new_std_price})
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price
        # update prices for average/standard cost products
        for move in self.filtered(
            lambda move: move._is_in()
            and move.with_company(move.company_id).product_id.cost_method in ["average", "standard"]
        ):
            move.update_prices()


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # def button_validate(self):
    #     for move in self.move_lines:
    #         if move.product_id.product_tmpl_id.trade_markup:
    #             move.product_id.product_tmpl_id.onchange_last_purchase_price()
    #     return super(StockPicking, self).button_validate()
