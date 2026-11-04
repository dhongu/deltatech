# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    cost_price_include_tax = fields.Boolean(string="Cost Price Includes Tax", default=False)
    cost_price_margin_percentage = fields.Float(string="Cost Price Margin Percentage", default=0.0)

    def _is_cost_price_protection_enabled(self):
        """Protecția prețului de cost extinde opțiunea standard „Hide Add To Cart” pentru
        produsele cu preț 0 (în 19.0 ``prevent_zero_price_sale``, în 20.0 ``prevent_sale`` cu
        ``prevent_sale_for == "zero_price"``)."""
        self.ensure_one()
        return self.prevent_sale and self.prevent_sale_for == "zero_price"
