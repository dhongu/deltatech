# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import Command, api, fields, models


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


class ProductProductLabelLine(models.TransientModel):
    _inherit = "product.product.label.line"

    price_incl = fields.Float("Price incl. Taxes", compute="_compute_price_incl", digits="Product Price")

    @api.depends("price", "product_id")
    def _compute_price_incl(self):
        for line in self:
            product = line.product_id
            company = self.env.company
            taxes = product.taxes_id.filtered(lambda t, c=company: t.company_id in c.parent_ids)
            line.price_incl = taxes.compute_all(line.price, company.currency_id, product=product)["total_included"]
