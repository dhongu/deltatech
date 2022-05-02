# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.tools.safe_eval import safe_eval


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
            from_currency = self.env.user.company_id.currency_id

            for seller in self.product_id.seller_ids:
                if seller.name == self.purchase_line_id.order_id.partner_id:
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

            return price_unit

        return super(StockMove, self)._get_price_unit()
