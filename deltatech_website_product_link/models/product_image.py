# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import werkzeug

from odoo import api, models


class ProductImage(models.Model):
    _inherit = "product.image"

    @api.onchange("name")
    def onchange_name(self):
        parsed_url = werkzeug.urls.url_parse(self.name)
        if parsed_url.scheme:
            data = self.product_tmpl_id.load_image_from_url(self.name)
            if data:
                self.name = self.name.split("/")[-1]
                self.image_1920 = data

    def write(self, vals):
        if "name" in vals:
            image_file_name = vals["name"]
            parsed_url = werkzeug.urls.url_parse(image_file_name)
            if parsed_url.scheme:
                data = self.product_tmpl_id.load_image_from_url(image_file_name)
                if data:
                    vals["name"] = image_file_name.split("/")[-1]
                    vals["image_1920"] = data
        return super(ProductImage, self).write(vals)
