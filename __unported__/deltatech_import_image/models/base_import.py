# ©  2020 Deltatech
# See README.rst file on addons root folder for license details


import base64
from urllib.parse import urlparse

import requests

from odoo import models
from odoo.tools import image


class BaseImport(models.TransientModel):
    _inherit = "base_import.import"

    def load_image_from_url(self, url):
        try:
            data = base64.b64encode(requests.get(url.strip()).content)  # .replace(b'\n', b'')
            image.base64_to_image(data)
        except Exception:
            data = False
        return data

    def _parse_import_data(self, data, import_fields, options):
        data = super(BaseImport, self)._parse_import_data(data, import_fields, options)
        all_fields = self.env[self.res_model].fields_get()
        for name, field in all_fields.items():
            if field["type"] in ["binary", "image"] and name in import_fields:
                index = import_fields.index(name)
                for line in data:
                    if not line[index]:
                        continue
                    parsed_url = urlparse(line[index])
                    if parsed_url.scheme:
                        line[index] = self.load_image_from_url(line[index])

        return data
