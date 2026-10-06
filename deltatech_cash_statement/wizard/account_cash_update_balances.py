# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL


class AccountCashUpdateBalances(models.TransientModel):
    _name = "account.cash.update.balances"
    _description = "Account Cash Update Balances"

    statement_id = fields.Many2one("account.bank.statement", readonly=True)
    journal_id = fields.Many2one(related="statement_id.journal_id")
    company_id = fields.Many2one(related="statement_id.company_id")
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id")
    mode = fields.Selection(
        [
            ("align", "Align with the accounting balance"),
            ("difference", "Register a cash difference"),
        ],
        default="align",
        required=True,
        help="Align: the starting balance of the first statement becomes the balance of the cash "
        "account before the statement date; no journal entry is created.\n"
        "Cash difference: the counted cash differs from the accounting balance; a dated "
        "statement line books the difference on the income or expense account.",
    )
    balance_start = fields.Monetary(string="Current Starting Balance", readonly=True)
    accounting_balance = fields.Monetary(
        readonly=True,
        help="Balance of the journal's cash account from the posted entries dated before the first selected statement.",
    )
    counted_balance = fields.Monetary(
        string="Counted Balance",
        help="Cash actually counted at the start of the statement date.",
    )
    difference = fields.Monetary(compute="_compute_difference")
    date = fields.Date(help="Date of the cash difference entry.")
    counterpart_account_id = fields.Many2one(
        "account.account",
        compute="_compute_counterpart_account_id",
        store=True,
        readonly=False,
        domain="[('company_ids', 'in', company_id)]",
        help="Surplus: income account (7588 in Romania). Shortage: expense account (6588), or "
        "the receivable from the person responsible (4282).",
    )
    label = fields.Char(default=lambda self: self.env._("Cash difference found at inventory"))

    @api.depends("journal_id")
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.journal_id.currency_id or wizard.company_id.currency_id

    @api.depends("counted_balance", "accounting_balance", "mode")
    def _compute_difference(self):
        for wizard in self:
            wizard.difference = (
                wizard.counted_balance - wizard.accounting_balance if wizard.mode == "difference" else 0.0
            )

    @api.depends("difference", "journal_id")
    def _compute_counterpart_account_id(self):
        for wizard in self:
            if wizard.currency_id.is_zero(wizard.difference):
                wizard.counterpart_account_id = False
                continue
            surplus = wizard.difference > 0
            account = wizard._ro_difference_account("7588" if surplus else "6588")
            if not account:
                account = wizard.journal_id.profit_account_id if surplus else wizard.journal_id.loss_account_id
            wizard.counterpart_account_id = account

    def _ro_difference_account(self, code):
        if self.company_id.account_fiscal_country_id.code != "RO":
            return self.env["account.account"]
        return self.env["account.account"].search(
            [("code", "=like", code + "%"), ("company_ids", "in", self.company_id.ids)], order="code", limit=1
        )

    @api.model
    def _selected_statements(self):
        active_ids = self.env.context.get("active_ids") or []
        return self.env["account.bank.statement"].search([("id", "in", active_ids)], order="date, id")

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        statements = self._selected_statements()
        if not statements:
            raise UserError(self.env._("Please select only Open or Posted statements"))
        if len(statements.journal_id) > 1:
            raise UserError(self.env._("Select statements of a single journal."))
        statement = statements[0]
        accounting_balance = self._get_accounting_balance(statement)
        defaults.update(
            {
                "statement_id": statement.id,
                "balance_start": statement.balance_start,
                "accounting_balance": accounting_balance,
                "counted_balance": accounting_balance,
                "date": statement.date,
            }
        )
        return defaults

    @api.model
    def _get_accounting_balance(self, statement):
        """Soldul contului de casă din notele postate datate înaintea extrasului."""
        journal = statement.journal_id
        account = journal.default_account_id
        if not account:
            return 0.0
        foreign = journal.currency_id and journal.currency_id != journal.company_id.currency_id
        self.env["account.move.line"].flush_model(["account_id", "date", "parent_state", "balance", "amount_currency"])
        self.env.cr.execute(
            SQL(
                """
                SELECT COALESCE(SUM(%(amount)s), 0)
                  FROM account_move_line
                 WHERE account_id = %(account_id)s
                   AND company_id = %(company_id)s
                   AND parent_state = 'posted'
                   AND date < %(date)s
                """,
                amount=SQL.identifier("amount_currency" if foreign else "balance"),
                account_id=account.id,
                company_id=journal.company_id.id,
                date=statement.date,
            )
        )
        return self.env.cr.fetchone()[0]

    def do_update_balance(self):
        self.ensure_one()
        statements = self._selected_statements()
        if self.mode == "difference" and not self.currency_id.is_zero(self.difference):
            self._create_difference_line()
        # Lanțul de solduri declarate se aliniază la ce e acum în contabilitate: soldul
        # inițial al primului extras este soldul contului, iar fiecare extras următor
        # pornește de la soldul final real al celui dinainte.
        balance_start = self._get_accounting_balance(self.statement_id)
        for statement in statements:
            statement.write({"balance_start": balance_start})
            statement.write({"balance_end_real": statement.balance_end})
            balance_start = statement.balance_end
        return {"type": "ir.actions.act_window_close"}

    def _create_difference_line(self):
        if not self.counterpart_account_id:
            raise UserError(self.env._("Select the account on which the cash difference is booked."))
        if not self.date:
            raise UserError(self.env._("Set the date of the cash difference."))
        self.env["account.bank.statement.line"].create(
            {
                "journal_id": self.journal_id.id,
                "statement_id": self.statement_id.id,
                "date": self.date,
                "payment_ref": self.label,
                "amount": self.difference,
                "counterpart_account_id": self.counterpart_account_id.id,
            }
        )
