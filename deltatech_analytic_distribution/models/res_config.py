from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    analytic_distribution_validation_enabled = fields.Boolean(
        string="Enable Analytic Distribution Validation",
        config_parameter="analytic_distribution_validation_enabled",
        help="Enable or disable the validation of analytic distribution in account moves.",
    )
