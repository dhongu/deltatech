# coding=utf-8


from odoo import api, fields, models, registry, _
from odoo.tools import float_is_zero


class ProductTemplate(models.Model):
    _inherit = "product.template"

    scrap = fields.Float(string="Scrap", help="A factor of 0.1 means a loss of 10% during the consumption.")