# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    product_weight_in_lbs = fields.Selection(selection_add=[("gram", "Gram")], config_parameter="product.weight_uom")
