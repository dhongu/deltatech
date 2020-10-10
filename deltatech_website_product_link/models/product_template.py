# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
from urllib.parse import urlparse

import requests

from odoo import api, fields, models
from odoo.tools import image


class ProductTemplate(models.Model):
    _inherit = "product.template"

    website_rewrite_id = fields.Many2one("website.rewrite")
    alternative_link = fields.Char(compute="_compute_alternative_link", inverse="_inverse_alternative_link")
    image_file_name = fields.Char(string="Image File Name")
    legacy_id = fields.Integer(string="Legacy ID")

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

    def load_image_from_url(self, url):
        try:
            data = base64.b64encode(requests.get(url.strip()).content)  # .replace(b'\n', b'')
            image.base64_to_image(data)
        except Exception:
            data = False
        return data

    @api.onchange("image_file_name")
    def onchange_image_file_name(self):
        parsed_url = urlparse(self.image_file_name)
        if parsed_url.scheme:
            data = self.load_image_from_url(self.image_file_name)
            if data:
                self.image_file_name = self.image_file_name.split("/")[-1]
                self.image_1920 = data

    def write(self, vals):
        if "image_file_name" in vals:
            image_file_name = vals["image_file_name"]
            parsed_url = urlparse(image_file_name)
            if parsed_url.scheme:
                data = self.load_image_from_url(image_file_name)
                if data:
                    vals["image_file_name"] = image_file_name.split("/")[-1]
                    vals["image_1920"] = data
        return super(ProductTemplate, self).write(vals)
