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


class ProductTemplate(models.Model):
    _inherit = "product.template"

    public_categ_id = fields.Many2one(
        "product.public.category", compute="_compute_public_categ_id", inverse="_inverse_public_categ_id", store=True
    )

    @api.depends("public_categ_ids")
    def _compute_public_categ_id(self):
        for product in self:
            if product.public_categ_ids:
                product.public_categ_id = product.public_categ_ids[0]
            else:
                product.public_categ_id = False

    def _inverse_public_categ_id(self):
        for product in self:
            if product.public_categ_id:
                product.public_categ_ids |= product.public_categ_id
            else:
                product.public_categ_ids = False
