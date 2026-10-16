# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountAnalyticDistributionModel(models.Model):
    _inherit = "account.analytic.distribution.model"

    team_id = fields.Many2one("crm.team", string="Sale team")
