from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mrp_alternative_partial = fields.Boolean(related="company_id.mrp_alternative_partial", readonly=False)
    mrp_alternative_on_assign = fields.Boolean(related="company_id.mrp_alternative_on_assign", readonly=False)
