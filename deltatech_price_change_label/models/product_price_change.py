# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class ProductPriceChange(models.Model):
    _inherit = "product.price.change"

    def action_print_labels(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "deltatech_product_labels.action_action_product_product_label"
        )
        action["context"] = {"active_model": self._name, "active_ids": self.ids}
        return action
