from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    can_modify_price_list_at_reception = fields.Boolean(
        related="company_id.can_modify_price_list_at_reception",
        readonly=False,
    )
