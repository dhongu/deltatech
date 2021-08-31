# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.tools import safe_eval


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_price_unit(self):
        """ Returns the unit price to store on the quant """
        if self.purchase_line_id:
            get_param = self.env["ir.config_parameter"].sudo().get_param
            update_product_price = get_param("purchase.update_product_price", default="False")
            update_product_price = safe_eval(update_product_price)

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

            return price_unit

        return super(StockMove, self)._get_price_unit()


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        for move in self.move_lines:
            if move.product_id.product_tmpl_id.trade_markup:
                move.product_id.product_tmpl_id.onchange_last_purchase_price()
        return super(StockPicking, self).button_validate()
