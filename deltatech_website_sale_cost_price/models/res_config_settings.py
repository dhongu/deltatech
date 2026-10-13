# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cost_price_include_tax = fields.Boolean(
        string="Cost Price Includes Tax",
        related="website_id.cost_price_include_tax",
        readonly=False,
    )
    cost_price_margin_percentage = fields.Float(
        related="website_id.cost_price_margin_percentage",
        readonly=False,
    )
