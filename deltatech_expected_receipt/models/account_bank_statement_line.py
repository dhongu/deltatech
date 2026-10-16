# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def action_card_settlement(self):
        """Deschide decontarea cu linia de extras deja aleasă."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Card Settlement"),
            "res_model": "deltatech.card.settlement",
            "views": [[False, "form"]],
            "target": "new",
            "context": {
                "default_statement_line_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }
