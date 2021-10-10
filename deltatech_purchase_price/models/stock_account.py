# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.tools.safe_eval import safe_eval


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_price_unit(self):
        """ Returns the unit price to store on the quant """
        if self.purchase_line_id:
            get_param = self.env["ir.config_parameter"].sudo().get_param

            update_product_price = safe_eval(get_param("purchase.update_product_price", default="True"))

            # este neidicat de a se forta actualizarea pretului standard
            update_standard_price = safe_eval(get_param("purchase.update_standard_price", default="False"))

            price_unit = self.purchase_line_id.with_context(date=self.date)._get_stock_move_price_unit()
            self.write({"price_unit": price_unit})  # mai trebuie sa pun o conditie de status ?
            # update price form last receipt
            for seller in self.product_id.seller_ids:
                if seller.name == self.purchase_line_id.order_id.partner_id:
                    if seller.min_qty == 0.0 and seller.date_start is False and seller.date_end is False:
                        from_currency = (
                            self.purchase_line_id.order_id.currency_id or self.env.user.company_id.currency_id
                        )
                        to_currency = seller.currency_id or self.env.user.company_id.currency_id
                        seller_price_unit = from_currency.compute(price_unit, to_currency)

                        if update_product_price:
                            seller.write({"price": seller_price_unit})

            # pretul standard se actualizeaza prin rutinele standard. Aici este o fortare pentru a se utliza ultimul pret
            if update_standard_price:
                self.product_id.write({"standard_price": price_unit})

            return price_unit

        return super(StockMove, self)._get_price_unit()
