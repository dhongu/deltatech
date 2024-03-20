# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountAnalyticDistributionModel(models.Model):
    _inherit = "account.analytic.distribution.model"

    # can_split_analytic = fields.Boolean(related="company_id.split_sale_analytic")
    can_split_analytic = fields.Boolean(compute="_compute_can_split")
    is_split_analytic_rule = fields.Boolean(string="This rule is for splitting")

    stock_analytic_id = fields.Many2one("account.analytic.account", string="Stock Analytic Account")
    margin_analytic_id = fields.Many2one("account.analytic.account", string="Margin Analytic Account")
    sale_team = fields.Many2one("crm.team", string="Sale team")

    def _compute_can_split(self):
        for analytic_default in self:
            res_company = analytic_default.company_id or self.env.user.company_id
            if res_company.split_sale_analytic:
                analytic_default.can_split_analytic = True
            else:
                analytic_default.can_split_analytic = False
