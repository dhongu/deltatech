# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64

import requests
import werkzeug

from odoo import api, fields, models, tools


class ProductTemplate(models.Model):
    _inherit = "product.template"

    image_file_name = fields.Char(string="Image File Name")

    def load_image_from_url(self, url):
        data = False
        try:
            req = requests.get(url.strip())
            if req.status_code == 200:
                data = base64.b64encode(req.content)
        except Exception:
            data = False
        return data

    @api.onchange("image_file_name")
    def onchange_image_file_name(self):
        if self.image_file_name:
            parsed_url = werkzeug.urls.url_parse(self.image_file_name)
            if parsed_url.scheme:
                data = self.load_image_from_url(self.image_file_name)
                if data:
                    self.image_file_name = self.image_file_name.split("/")[-1]
                    vals = {"image": data}
                    tools.image_resize_images(vals)
                    self.image = vals["image"]
                    self.image_medium = vals["image_medium"]

    def write(self, vals):
        if "image_file_name" in vals:
            image_file_name = vals["image_file_name"]
            parsed_url = werkzeug.urls.url_parse(image_file_name)
            if parsed_url.scheme:
                data = self.load_image_from_url(image_file_name)
                if data:
                    vals["image_file_name"] = image_file_name.split("/")[-1]
                    vals["image"] = data
        return super(ProductTemplate, self).write(vals)
