# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    website_visible = fields.Boolean(
        string="Website visible",
        compute="_compute_website_visible",
        store=True,
        index=True,
    )

    @api.depends("product_attribute_value_id.visibility")
    def _compute_website_visible(self):
        for rec in self:
            rec.website_visible = bool(rec.product_attribute_value_id and rec.product_attribute_value_id.visibility == "visible")

    def _only_active(self):
        res = super()._only_active()
        if self.env.context.get("website_id") and res:
            # use precomputed stored field to filter in DB
            res = self.search([("id", "in", res.ids), ("website_visible", "=", True)])
        return res
