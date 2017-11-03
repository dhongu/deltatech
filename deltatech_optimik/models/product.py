# coding=utf-8

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

import odoo.addons.decimal_precision as dp


class ProductCategory(models.Model):
    _inherit = "product.category"

    optimik = fields.Boolean('Relevant optimik')
