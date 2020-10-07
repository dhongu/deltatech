# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import base64

from odoo import api, fields, models, tools
from odoo.modules import get_module_resource


class PropertyLand(models.Model):
    _name = "property.land"
    _description = "Land"
    _inherit = "property.property"

    location_type = fields.Selection([("I", "Intravilan"), ("E", "Extravilan")], default="E")

    tarla = fields.Char()  # required=True)
    parcela = fields.Char(string="Parcela cadastrală")
    sector = fields.Char(string="Sector cadastral")
    bloc_fizic = fields.Char(string="Nr bloc fizic")

    carte = fields.Char(string="Carte funciară")
    utr = fields.Char(string="UTR")
    categ_id = fields.Many2one("property.land.categ", string="Category")

    cod = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("import_file"):
            self._check_import_consistency(vals_list)
        for vals in vals_list:
            if not vals.get("image"):
                vals["image"] = self._get_default_image()
            tools.image_resize_images(vals, sizes={"image": (1024, None)})

        buildings = super(PropertyLand, self).create(vals_list)

        return buildings

    @api.model
    def _get_default_image(self):
        if self._context.get("install_mode"):
            return False

        colorize, img_path, image = False, False, False

        img_path = get_module_resource("deltatech_property", "static/src/img", "land.png")
        colorize = True

        if img_path:
            with open(img_path, "rb") as f:
                image = f.read()
        if image and colorize:
            image = tools.image_colorize(image)

        return tools.image_resize_image_big(base64.b64encode(image))
