# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    alternative_link = fields.Char()

    def _compute_website_url(self):
        super(ProductPublicCategory, self)._compute_website_url()
        origin = self.env.context.get("origin", False)
        if not origin:
            for category in self:
                if category.alternative_link:
                    website_url = category.alternative_link
                    if website_url[0] != "/":
                        website_url = "/" + website_url
                    category.website_url = website_url
