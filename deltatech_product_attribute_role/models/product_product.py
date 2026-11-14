# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_attribute_value_by_role(self, role):
        """The variant's value for the attribute holding `role`, or an empty
        recordset when the variant has none."""
        ptav = self.product_template_attribute_value_ids.filtered(lambda p: p.attribute_id.attribute_role == role)
        return ptav[:1].product_attribute_value_id
