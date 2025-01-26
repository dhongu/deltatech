# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, models
from odoo.exceptions import AccessError


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _change_standard_price(self, new_price):
        if self.qty_available and not self.env.user.has_group("deltatech_stock_account.group_change_standard_price"):
            raise AccessError(_("You are not allowed to change the cost price of a product."))

        return super()._change_standard_price(new_price)
