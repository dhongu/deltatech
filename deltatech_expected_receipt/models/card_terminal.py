# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Terminalele de card: aparatul cu care se încasează și contul bancar în care virează banca.

Toate setările stau pe terminal, nu pe companie: jurnalul, fereastra de potrivire și pragul
de alertă diferă de la o bancă la alta.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CardTerminal(models.Model):
    _name = "deltatech.card.terminal"
    _description = "Card Terminal"
    _order = "sequence, name"
    _check_company_auto = True

    name = fields.Char("Terminal", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", required=True, index=True, default=lambda self: self.env.company)
    user_id = fields.Many2one(
        "res.users",
        "Default For",
        index="btree_not_null",
        help="When this user registers a card payment, the terminal is selected automatically.",
    )
    journal_id = fields.Many2one(
        "account.journal",
        "Bank Journal",
        required=True,
        check_company=True,
        domain="[('type', '=', 'bank')]",
        help="The bank account in which the bank transfers the card payments. The payment waits on the "
        "suspense account of this journal (5125 Amounts in course of settlement) until the bank "
        "statement line arrives.",
    )
    settlement_account_id = fields.Many2one(
        related="journal_id.suspense_account_id", string="Settlement Account", readonly=True
    )
    settle_window_days = fields.Integer(
        "Matching Window (days)",
        default=4,
        help="How many days before the bank statement date the receipts are searched.",
    )
    late_days = fields.Integer(
        "Alert After (days)",
        default=3,
        help="A receipt not settled after this many days is shown as late.",
    )
    receipt_count = fields.Integer("Receipts", compute="_compute_receipt_count")

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "A terminal with this name already exists.",
    )

    def _compute_receipt_count(self):
        counts = dict(
            self.env["deltatech.expected.receipt"]._read_group(
                [("terminal_id", "in", self.ids)], ["terminal_id"], ["__count"]
            )
        )
        for terminal in self:
            terminal.receipt_count = counts.get(terminal, 0)

    @api.constrains("settle_window_days", "late_days")
    def _check_days(self):
        for terminal in self:
            if terminal.settle_window_days < 0 or terminal.late_days < 0:
                raise ValidationError(self.env._("The number of days cannot be negative."))

    @api.constrains("user_id", "company_id", "active")
    def _check_one_terminal_per_user(self):
        """Un utilizator are cel mult un terminal implicit, altfel alegerea automată n-ar mai
        avea un răspuns unic."""
        for terminal in self.filtered("user_id"):
            twin = self.with_context(active_test=False).search(
                [
                    ("id", "!=", terminal.id),
                    ("user_id", "=", terminal.user_id.id),
                    ("company_id", "=", terminal.company_id.id),
                ],
                limit=1,
            )
            if twin:
                raise ValidationError(
                    self.env._(
                        "%(user)s already has terminal %(twin)s. A user can have only one default terminal.",
                        user=terminal.user_id.name,
                        twin=twin.name,
                    )
                )

    @api.model
    def _default_for_user(self, user=None):
        user = user or self.env.user
        terminal = self.search([("user_id", "=", user.id), ("company_id", "=", self.env.company.id)], limit=1)
        if not terminal:
            # Un singur terminal în companie: nu are rost să-l mai aleagă cineva.
            terminals = self.search([("company_id", "=", self.env.company.id)], limit=2)
            terminal = terminals if len(terminals) == 1 else terminal
        return terminal

    def action_open_receipts(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("deltatech_expected_receipt.action_expected_receipt")
        action["domain"] = [("terminal_id", "=", self.id)]
        action["context"] = {}
        return action
