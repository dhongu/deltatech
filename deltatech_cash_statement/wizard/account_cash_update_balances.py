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
    statement_ids = fields.Many2many("account.bank.statement", string="Statements")
    journal_ids = fields.Many2many("account.journal", string="Journals", compute="_compute_journal_ids")
    multi_journal = fields.Boolean(compute="_compute_journal_ids")
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
    partner_id = fields.Many2one(
        "res.partner",
        string="Responsible Person",
        help="The person the shortage is charged to (4282). The receivable is followed on this partner.",
    )
    partner_required = fields.Boolean(compute="_compute_partner_required")
    label = fields.Char(default=lambda self: self.env._("Cash difference found at inventory"))

    @api.depends("counterpart_account_id")
    def _compute_partner_required(self):
        for wizard in self:
            account = wizard.counterpart_account_id
            wizard.partner_required = bool(account) and (
                account.account_type == "asset_receivable" or (account.code or "").startswith("428")
            )

    @api.depends("statement_ids")
    def _compute_journal_ids(self):
        for wizard in self:
            wizard.journal_ids = wizard.statement_ids.journal_id
            wizard.multi_journal = len(wizard.journal_ids) > 1

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
        statement = statements[0]
        accounting_balance = self._get_accounting_balance(statement)
        defaults.update(
            {
                "statement_id": statement.id,
                "statement_ids": [(6, 0, statements.ids)],
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
        # Extrasele vin din câmpul asistentului, nu din active_ids-ul contextului de la buton.
        statements = self.statement_ids or self.statement_id
        if self.mode == "difference" and len(statements.journal_id) > 1:
            raise UserError(self.env._("A cash difference can be registered for one journal at a time."))
        if self.mode == "difference" and not self.currency_id.is_zero(self.difference):
            self._create_difference_line()
        # Lanțul de solduri declarate se aliniază la ce e acum în contabilitate, separat pe
        # fiecare jurnal (deci pe companie și monedă), ca în standard: soldul inițial al primului
        # extras al jurnalului este soldul contului lui de casă, iar fiecare extras următor
        # (după dată, apoi id) pornește de la soldul final real al celui dinainte din același jurnal.
        for journal in statements.journal_id:
            chain = statements.filtered(lambda st, journal=journal: st.journal_id == journal).sorted(
                lambda st: (st.date, st.id)
            )
            balance_start = self._get_accounting_balance(chain[0])
            for statement in chain:
                statement.write({"balance_start": balance_start})
                statement.write({"balance_end_real": statement.balance_end})
                balance_start = statement.balance_end
        return {"type": "ir.actions.act_window_close"}

    def _create_difference_line(self):
        if not self.counterpart_account_id:
            raise UserError(self.env._("Select the account on which the cash difference is booked."))
        if not self.date:
            raise UserError(self.env._("Set the date of the cash difference."))
        if self.date < self.statement_id.date:
            # O dată anterioară extrasului ar număra diferența de două ori: o dată în soldul
            # contabil de la începutul extrasului și încă o dată în liniile lui.
            raise UserError(self.env._("The cash difference cannot be dated before the statement."))
        if self.partner_required and not self.partner_id:
            raise UserError(self.env._("Select the person the cash shortage is charged to."))
        self.env["account.bank.statement.line"].create(
            {
                "journal_id": self.journal_id.id,
                "statement_id": self.statement_id.id,
                "date": self.date,
                "payment_ref": self.label,
                "amount": self.difference,
                "counterpart_account_id": self.counterpart_account_id.id,
                "partner_id": self.partner_id.id,
            }
        )
