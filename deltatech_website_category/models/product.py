# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models

from odoo.addons.http_routing.models.ir_http import slug


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    active = fields.Boolean(
        "Active", default=True, help="If unchecked, it will allow you to hide the category without removing it."
    )

    website_url = fields.Char(
        "Website URL", compute="_compute_website_url", help="The full URL to access the document through the website."
    )

    @api.depends_context("lang")
    def _compute_website_url(self):
        for category in self:
            category.website_url = "/shop/category/%s" % slug(category)
