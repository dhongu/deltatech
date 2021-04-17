# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    alternative_link = fields.Char()
    legacy_id = fields.Integer(string="Legacy ID")

    def _compute_website_url(self):
        record = super(ProductTemplate, self)._compute_website_url()
        origin = self.env.context.get("origin", False)
        if not origin:
            for product in self:
                if product.alternative_link:
                    website_url = product.alternative_link
                    if website_url[0] != "/":
                        website_url = "/" + website_url
                    product.website_url = website_url
        return record
