# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # În 20.0 `cumulated_balance` standard se calculează doar pe un domeniu cu un singur cont (fără filtru pe
    # partener): fișa 542 a angajatului (cont + partener) ar arăta mereu zero, de aceea are soldul ei cumulat.
    expenses_cumulated_balance = fields.Monetary(
        string="Running Balance",
        compute="_compute_expenses_cumulated_balance",
        currency_field="company_currency_id",
        exportable=False,
        help="Cumulated balance of the lines listed, in the order of the list (the oldest line first).",
    )

    @api.depends_context("order_cumulated_balance", "domain_cumulated_balance")
    def _compute_expenses_cumulated_balance(self):
        domain = self.env.context.get("domain_cumulated_balance")
        order = self.env.context.get("order_cumulated_balance")
        if domain is None or not order:
            # nu venim dintr-o listă (search_fetch): soldul cumulat nu are sens
            self.expenses_cumulated_balance = 0.0
            return
        # toate liniile listei (fișa unui angajat pe 542), în ordinea listei; soldul se cumulează de la cea mai veche
        lines = self.sudo().with_context(active_test=False).search(list(domain), order=order)
        cumulated = {}
        balance = 0.0
        for line in reversed(lines):
            balance += line.balance
            cumulated[line.id] = balance
        for line in self:
            line.expenses_cumulated_balance = cumulated.get(line._origin.id, 0.0)
