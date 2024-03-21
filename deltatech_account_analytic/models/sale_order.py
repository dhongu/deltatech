# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("partner_id", "date_order", "team_id")
    def _compute_analytic_account_id(self):
        for order in self:
            if order.team_id:
                default = self.env["account.analytic.default"].search([("sale_team", "=", order.team_id.id)], limit=1)
                if default:
                    order.analytic_account_id = default.analytic_id
            else:
                super(SaleOrder, order)._compute_analytic_account_id()
