# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_analytic_distribution(self):
        """
        Cautare dupa team_id
        :return: None
        """
        res = super()._compute_analytic_distribution()
        for line in self:
            if (
                line.display_type == "product"
                and line.move_id.move_type in ["out_invoice", "out_refund"]
                and line.move_id.team_id
            ):
                distributions = self.env["account.analytic.distribution.model"].search(
                    [("team_id", "=", line.move_id.team_id.id)]
                )
                if distributions and len(distributions) == 1:
                    line.analytic_distribution = distributions.analytic_distribution
        return res

    def _prepare_analytic_lines(self):
        res = super()._prepare_analytic_lines()
        if self.move_id.move_type in ["in_invoice", "in_refund"]:
            for line in res:
                if line["account_id"]:
                    # se presupune ca numele echipei = nume analitic, deocamdata
                    analytic_account_id = self.env["account.analytic.account"].sudo().browse(line["account_id"])
                    sale_team = self.env["crm.team"].sudo().search([("name", "=", analytic_account_id.name)])
                    if sale_team:
                        line["team_id"] = sale_team.id
        return res
