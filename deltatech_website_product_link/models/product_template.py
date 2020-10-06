# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    website_rewrite_id = fields.Many2one("website.rewrite")
    alternative_link = fields.Char(compute="_compute_alternative_link", inverse="_inverse_alternative_link")

    def _compute_alternative_link(self):
        for product in self:
            product.alternative_link = product.website_rewrite_id.url_from

    def _inverse_alternative_link(self):
        for product in self:
            if product.alternative_link:
                if not product.website_rewrite_id:
                    product.website_rewrite_id = self.env["website.rewrite"].create(
                        {
                            "redirect_type": "301",
                            "name": product.name,
                            "url_from": product.alternative_link,
                            "url_to": product.website_url,
                        }
                    )
                else:
                    product.website_rewrite_id.write(
                        {"name": product.name, "url_from": product.alternative_link, "url_to": product.website_url}
                    )
            else:
                if product.website_rewrite_id:
                    product.website_rewrite_id.unlink()
