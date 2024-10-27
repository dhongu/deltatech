# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"

    def get_negative_products(self):
        """
        Gets location's negative products
        :return: list of dicts with product_id and negative quantity
        """
        self.ensure_one()
        products_dict = []
        quants = self.env["stock.quant"].search([("location_id", "child_of", self.id), ("quantity", "<", 0)])
        for quant in quants:
            if quant.product_id in products_dict:
                products_dict[quant.product_id] += quant.quantity
            else:
                products_dict.append({quant.product_id: quant.quantity})
        return products_dict

    def send_mail_negative_stock(self):
        self.ensure_one()
        products = self.get_negative_products()
        if products and self.user_id:
            template_id = self.env.ref("deltatech_move_negative_stock.mail_template_negative_stock")
            template_id.send_mail(self.id, False, False)
