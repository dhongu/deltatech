# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    @api.model
    def default_get(self, fields):
        # the purchase product views pass default_price=standard_price:
        # a new vendor pricing row must not start at the product cost
        if "default_price" in self.env.context:
            self = self.with_context(default_price=0.0)  # pylint: disable=self-cls-assignment
        return super().default_get(fields)
