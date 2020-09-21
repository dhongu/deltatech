# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.osv import expression

import odoo.addons.decimal_precision as dp


class ProductCategory(models.Model):
    _inherit = "product.category"

    way_production = fields.Selection(
        [
            ("consumption", "Consumption in production"),
            ("receipt", "Receipt from production"),
            ("both", "Consumption and Receipt"),
        ],
        default="both",
        string="Production Way",
    )
