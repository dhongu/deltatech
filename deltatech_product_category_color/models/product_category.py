# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import random

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    color = fields.Integer(string="Color Index", default=lambda self: random.randint(1, 11))
