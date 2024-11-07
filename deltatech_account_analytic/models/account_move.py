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
