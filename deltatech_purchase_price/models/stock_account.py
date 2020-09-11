# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _get_price_unit(self):
        """ Returns the unit price to store on the quant """
        if self.purchase_line_id:
            get_param = self.env["ir.config_parameter"].sudo().get_param
            update_supplier_price = get_param(
                "purchase.update_supplier_price", default=True
            )  # mai bine era update_supplier_price
            if update_supplier_price == "False":
                update_supplier_price = False

            update_product_standard_price = get_param("purchase.update_product_standard_price", default=False)
            if update_product_standard_price == "False":
                update_product_standard_price = False

            price_unit = self.purchase_line_id.with_context(date=self.date)._get_stock_move_price_unit()
            if update_product_standard_price:
                product_template = self.product_id.product_tmpl_id
                msg_body = "Update purchase price from PO %s:\nOld price: %s -> New price: %s" % (
                    self.purchase_line_id.order_id.name,
                    product_template.standard_price,
                    self.price_unit,
                )
                product_template.message_post(body=msg_body)
                self.product_id.write({"standard_price": price_unit})

            self.write({"price_unit": price_unit})  # mai trebuie sa pun o conditie de status ?
            # update price form last receipt
            for seller in self.product_id.seller_ids:
                if seller.name == self.purchase_line_id.order_id.partner_id:
                    if seller.min_qty <= 1.0 and seller.date_start is False and seller.date_end is False:
                        if seller.currency_id:
                            if seller.currency_id == self.purchase_line_id.order_id.currency_id:
                                seller_price_unit = self.purchase_line_id.price_unit
                            else:
                                seller_price_unit = self.env.user.company_id.currency_id.compute(
                                    price_unit, seller.currency_id
                                )
                        else:
                            seller_price_unit = price_unit
                        if update_supplier_price:
                            seller.write({"price": seller_price_unit})

            return price_unit

        return super(StockMove, self)._get_price_unit()

    @api.multi
    def product_price_update_before_done(self, forced_qty=None):

        super(StockMove, self.with_context(force_fifo_to_average=True)).product_price_update_before_done(forced_qty)
