from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    analytic_distribution_validation_enabled = fields.Boolean(
        string="Enable Analytic Distribution Validation",
        help="Enforce that analytic lines have 100% distribution for this company.",
    )
