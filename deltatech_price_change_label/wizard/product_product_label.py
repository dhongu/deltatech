# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import Command, api, models


class ProductProductLabel(models.TransientModel):
    _inherit = "product.product.label"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "product.price.change":
            changes = self.env["product.price.change"].browse(self.env.context.get("active_ids", []))
            res["label_lines"] = self.get_price_change_lines(changes)
        return res

    @api.model
    def get_price_change_lines(self, changes):
        """One label for each product with a changed price, the variants of a template included"""
        products = self.env["product.product"]
        for line in changes.line_ids:
            products |= line.product_id or line.product_template_id.product_variant_ids
        return [Command.create({"product_id": product.id, "quantity": 1}) for product in products]
