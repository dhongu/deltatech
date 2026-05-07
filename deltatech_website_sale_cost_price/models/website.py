# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    cost_price_include_tax = fields.Boolean(string="Cost Price Includes Tax", default=False)
    cost_price_margin_percentage = fields.Float(string="Cost Price Margin Percentage", default=0.0)
