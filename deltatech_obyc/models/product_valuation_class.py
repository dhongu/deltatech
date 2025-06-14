# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductValuationClass(models.Model):
    _name = "product.valuation.class"
    _description = "Valuation Class"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
