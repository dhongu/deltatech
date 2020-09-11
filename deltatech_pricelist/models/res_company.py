from odoo import api, fields, models


class Company(models.Model):
    _inherit = "res.company"

    @api.model
    def _default_price_currency(self):
        return self.env.ref("base.EUR")

    price_currency_id = fields.Many2one("res.currency", string="Price List Currency", default=_default_price_currency)
