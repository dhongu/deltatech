# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_length = fields.Float(string="Length", default=1)
    product_width = fields.Float(string="Width", default=1)
    product_height = fields.Float(string="Height", default=1)

    @api.onchange("product_length", "product_width", "product_height")
    def _onchange_dimension(self):
        # dimensions are in cm; the product is in m3, converted to the configured volume unit
        volume_m3 = self.product_length * self.product_width * self.product_height / 1000000
        cubic_meter = self.env.ref("uom.product_uom_cubic_meter")
        volume_uom = self._get_volume_uom_id_from_ir_config_parameter()
        self.volume = cubic_meter._compute_quantity(volume_m3, volume_uom, round=False)
