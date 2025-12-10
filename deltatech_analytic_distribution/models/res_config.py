from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    analytic_distribution_validation_enabled = fields.Boolean(
        related="company_id.analytic_distribution_validation_enabled",
        readonly=False,
        string="Enable Analytic Distribution Validation",
        help="Enable or disable analytic distribution enforcement for this company.",
    )
