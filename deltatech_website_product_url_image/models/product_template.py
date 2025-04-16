# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import logging

import requests
import werkzeug
from odoo import api, fields, models
from odoo.tools import image

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    image_file_name = fields.Char(string="Image File Name")

    def load_image_from_url(self, url):
        try:
            data = requests.get(url.strip(), timeout=10).content
            # data = base64.b64encode(requests.get(url.strip(), timeout=10).content)  # .replace(b'\n', b'')
            # image.base64_to_image(data)
            if url.endswith(".webp"):
                data = base64.b64encode(data)
                return data
            data = image.binary_to_image(data)
        except Exception as e:
            _logger.warning(f"Error loading image from url {url}: {e}")
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
                    self.image_1920 = data

    def write(self, vals):
        if "image_file_name" in vals:
            image_file_name = vals["image_file_name"]
            parsed_url = werkzeug.urls.url_parse(image_file_name)
            if parsed_url.scheme:
                data = self.load_image_from_url(image_file_name)
                if data:
                    vals["image_file_name"] = image_file_name.split("/")[-1]
                    vals["image_1920"] = data
        return super().write(vals)
