# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    user_id = fields.Many2one(
        "res.users",
        string="Manager",
        help="User notified by the daily cron when this location holds negative stock.",
    )

    def get_negative_products(self):
        """Get the negative quantities of this location, aggregated per product.

        Only the negative quants are taken into account, so a product stored in
        several sub-locations is reported once, with the sum of its negative
        quantities (positive quants of the same product are not netted out).

        :return: dict {product record: negative quantity (float, always < 0)}
        """
        self.ensure_one()
        products = {}
        quants = self.env["stock.quant"].search([("location_id", "child_of", self.id), ("quantity", "<", 0)])
        for quant in quants:
            products[quant.product_id] = products.get(quant.product_id, 0.0) + quant.quantity
        return products

    def send_mail_negative_stock(self):
        self.ensure_one()
        # Without a manager there is nobody to notify, so the location is skipped
        # instead of letting the daily cron fail on an empty recipient.
        if not self.user_id:
            return False
        products = self.get_negative_products()
        if not products:
            return False
        template_id = self.env.ref("deltatech_move_negative_stock.mail_template_negative_stock")
        template_id.send_mail(self.id, False, False)
        return True
