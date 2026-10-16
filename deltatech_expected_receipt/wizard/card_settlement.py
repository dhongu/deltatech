# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Decontarea: desface suma globală virată de bancă pe încasările cu cardul.

Banca trimite o singură linie pe zi, fără detalii. Ecranul caută grupul de încasări în
așteptare a căror sumă dă exact linia și le reconciliază pe toate odată, pe contul de
decontare (5125). Trei reguli:

- potrivirea e la ban: comisionul băncii vine pe o linie separată, deci o diferență înseamnă
  un grup greșit, nu un comision lipsă;
- dacă ies două combinații, ecranul nu alege: le arată și lasă omul să bifeze;
- fereastra de căutare e cea a terminalului (implicit T-4…T).
"""

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo.tools.misc import formatLang

from ..models.expected_receipt import MAX_CANDIDATES


class CardSettlement(models.TransientModel):
    _name = "deltatech.card.settlement"
    _description = "Card Settlement"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    statement_line_id = fields.Many2one(
        "account.bank.statement.line",
        "Statement Line",
        check_company=True,
        domain="[('is_reconciled', '=', False), ('amount', '>', 0), ('company_id', '=', company_id)]",
        help="The grouped amount transferred by the bank.",
    )
    terminal_id = fields.Many2one(
        "deltatech.card.terminal",
        "Terminal",
        check_company=True,
        help="Empty: all the terminals that pay into the statement line's journal.",
    )
    date = fields.Date("Statement Date", related="statement_line_id.date")
    amount = fields.Monetary("Amount to Settle", related="statement_line_id.amount")
    currency_id = fields.Many2one(related="statement_line_id.currency_id")
    state = fields.Selection(
        [
            ("search", "To Search"),
            ("proposed", "Combination Found"),
            ("ambiguous", "Several Combinations"),
            ("manual", "Select Manually"),
        ],
        default="search",
        required=True,
    )
    message = fields.Text(readonly=True)
    line_ids = fields.One2many("deltatech.card.settlement.line", "settlement_id", "Pending Receipts")
    selected_total = fields.Monetary(compute="_compute_selected_total")
    selected_count = fields.Integer("Selected", compute="_compute_selected_total")
    difference = fields.Monetary(compute="_compute_selected_total")
    can_settle = fields.Boolean(compute="_compute_selected_total")

    @api.depends("line_ids.selected", "line_ids.amount", "amount", "currency_id")
    def _compute_selected_total(self):
        for wizard in self:
            chosen = wizard.line_ids.filtered("selected")
            total = sum(chosen.mapped("amount"))
            wizard.selected_count = len(chosen)
            wizard.selected_total = total
            wizard.difference = wizard.amount - total
            rounding = (wizard.currency_id or wizard.company_id.currency_id).rounding
            wizard.can_settle = bool(total) and float_is_zero(wizard.difference, precision_rounding=rounding)

    def _window_days(self):
        terminals = self.terminal_id or self.env["deltatech.card.terminal"].search(
            [("journal_id", "=", self.statement_line_id.journal_id.id)]
        )
        return max(terminals.mapped("settle_window_days") or [4])

    def _money(self, amount):
        return formatLang(self.env, amount or 0.0, currency_obj=self.currency_id or self.company_id.currency_id)

    # ------------------------------------------------------------------
    def action_search(self):
        self.ensure_one()
        statement = self.statement_line_id
        if not statement:
            raise UserError(self.env._("Select the bank statement line first."))
        if statement.is_reconciled:
            raise UserError(self.env._("The bank statement line is already reconciled."))
        if float_compare(self.amount, 0.0, precision_rounding=self.currency_id.rounding) <= 0:
            raise UserError(self.env._("Card payments are settled on incoming statement lines."))
        Receipt = self.env["deltatech.expected.receipt"]
        window = self._window_days()
        candidates = Receipt._candidates_for_statement(statement, terminal=self.terminal_id, window_days=window)
        self.line_ids.unlink()
        if not candidates:
            self.write(
                {
                    "state": "manual",
                    "message": self.env._(
                        "No pending card receipt on journal %(journal)s between %(start)s and %(end)s.",
                        journal=statement.journal_id.display_name,
                        start=fields.Date.to_string(fields.Date.subtract(statement.date, days=window)),
                        end=fields.Date.to_string(statement.date),
                    ),
                }
            )
            return self._reopen()
        solutions, reason = Receipt._find_exact_combinations(candidates, self.amount, self.currency_id)
        self._fill_lines(candidates, solutions)
        self.write(self._result_values(candidates, solutions, reason))
        return self._reopen()

    def action_select_none(self):
        self.ensure_one()
        self.line_ids.selected = False
        return self._reopen()

    def _fill_lines(self, candidates, solutions):
        """Scrie rândurile de bifat; bifează doar când soluția e unică."""
        first = solutions[0] if len(solutions) == 1 else self.env["deltatech.expected.receipt"]
        belongs = {}
        for index, solution in enumerate(solutions, start=1):
            for receipt in solution:
                belongs.setdefault(receipt.id, []).append(str(index))
        self.line_ids = [
            Command.create(
                {
                    "receipt_id": receipt.id,
                    "selected": receipt in first,
                    "combo": ", ".join(belongs.get(receipt.id, [])),
                }
            )
            for receipt in candidates
        ]

    def _result_values(self, candidates, solutions, reason):
        if reason == "too_many":
            return {
                "state": "manual",
                "message": self.env._(
                    "There are more than %s pending receipts in the window, too many for a combination "
                    "search. Select a terminal or tick the receipts manually.",
                    MAX_CANDIDATES,
                ),
            }
        if reason == "too_complex":
            return {
                "state": "manual",
                "message": self.env._(
                    "The amount exceeds the safety limit of the automatic search. Tick the receipts manually."
                ),
            }
        if not solutions:
            total = sum(candidates.mapped("amount"))
            hint = ""
            if total < self.amount:
                hint = self.env._(
                    " %s is missing: probably a card payment was not registered.", self._money(self.amount - total)
                )
            return {
                "state": "manual",
                "message": self.env._(
                    "No combination gives exactly %(amount)s. %(count)s pending receipts in the window, "
                    "%(total)s in total.%(hint)s\nThe match is exact to the cent: the bank fee comes on a "
                    "separate line.",
                    amount=self._money(self.amount),
                    count=len(candidates),
                    total=self._money(total),
                    hint=hint,
                ),
            }
        if len(solutions) == 1:
            return {
                "state": "proposed",
                "message": self.env._(
                    "Exactly one combination found: %(count)s receipts give %(amount)s to the cent. Check it "
                    "and press 'Settle'.",
                    count=len(solutions[0]),
                    amount=self._money(self.amount),
                ),
            }
        return {
            "state": "ambiguous",
            "message": self.env._(
                "Several combinations give exactly %s; the choice is yours. The 'Combination' column shows "
                "which one each receipt belongs to: tick the right group and press 'Settle'.",
                self._money(self.amount),
            ),
        }

    # ------------------------------------------------------------------
    def action_settle(self):
        """Reconciliază grupul bifat cu linia de extras, pe contul de decontare."""
        self.ensure_one()
        if not self.env.user.has_group("deltatech_expected_receipt.group_manager"):
            raise UserError(self.env._("Only an expected receipts manager can settle card payments."))
        statement = self.statement_line_id
        if not statement or statement.is_reconciled:
            raise UserError(self.env._("The bank statement line is no longer available."))
        receipts = self.line_ids.filtered("selected").receipt_id
        if not receipts:
            raise UserError(self.env._("Tick the receipts that make up the statement line."))
        # Starea se recitește: între căutare și decontare cineva poate fi reconciliat sau
        # anulat o încasare.
        receipts.invalidate_recordset(["state"])
        wrong = receipts.filtered(lambda r: r.state != "pending")
        if wrong:
            raise UserError(
                self.env._("%s is no longer pending; search again.", ", ".join(wrong.mapped("display_name")))
            )
        rounding = self.currency_id.rounding
        selected_total = sum(receipts.mapped("amount"))
        if not float_is_zero(self.amount - selected_total, precision_rounding=rounding):
            raise UserError(
                self.env._(
                    "The ticked receipts give %(selected)s and the statement line is %(amount)s: the match "
                    "must be exact.",
                    selected=self._money(selected_total),
                    amount=self._money(self.amount),
                )
            )
        receipt_lines = receipts._settlement_lines()
        if len(receipt_lines) != len(receipts):
            raise UserError(self.env._("One of the ticked receipts was reconciled meanwhile; search again."))
        _liquidity, suspense_lines, _other = statement._seek_for_lines()
        suspense_lines = suspense_lines.filtered(lambda line: not line.reconciled)
        if not suspense_lines:
            raise UserError(self.env._("The statement line has nothing left on the suspense account."))
        if set(receipt_lines.account_id.ids) != set(suspense_lines.account_id.ids):
            raise UserError(
                self.env._(
                    "The receipts wait on %(receipts)s and the statement line on %(statement)s.",
                    receipts=", ".join(receipt_lines.account_id.mapped("display_name")),
                    statement=", ".join(suspense_lines.account_id.mapped("display_name")),
                )
            )
        (receipt_lines | suspense_lines).sudo().reconcile()
        receipts.invalidate_recordset()
        settled = receipts.filtered(lambda r: r._payment_is_reconciled())
        settled.sudo().write({"state": "settled", "settlement_date": statement.date, "statement_line_id": statement.id})
        if settled != receipts:
            raise UserError(
                self.env._(
                    "The reconciliation remained partial for %s.",
                    ", ".join((receipts - settled).mapped("display_name")),
                )
            )
        for receipt in settled:
            receipt.message_post(
                body=self.env._(
                    "Settled by the bank statement of %(date)s (%(amount)s).",
                    date=fields.Date.to_string(statement.date),
                    amount=self._money(self.amount),
                ),
                subtype_xmlid="mail.mt_note",
            )
        action = self.env["deltatech.expected.receipt"]._action_for_domain([("id", "in", settled.ids)])
        action["name"] = self.env._("Settled Receipts")
        return action

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Card Settlement"),
            "res_model": self._name,
            "res_id": self.id,
            "views": [[False, "form"]],
            "target": "new",
        }


class CardSettlementLine(models.TransientModel):
    _name = "deltatech.card.settlement.line"
    _description = "Card Settlement Line"
    _order = "date desc, id"

    settlement_id = fields.Many2one("deltatech.card.settlement", required=True, ondelete="cascade", index=True)
    receipt_id = fields.Many2one("deltatech.expected.receipt", "Receipt", required=True, ondelete="cascade")
    selected = fields.Boolean("Settle")
    combo = fields.Char("Combination", readonly=True, help="The combination(s) found that include this receipt.")
    partner_id = fields.Many2one(related="receipt_id.partner_id")
    date = fields.Date(related="receipt_id.date")
    amount = fields.Monetary(related="receipt_id.amount")
    currency_id = fields.Many2one(related="receipt_id.currency_id")
    terminal_id = fields.Many2one(related="receipt_id.terminal_id")
    document_name = fields.Char(related="receipt_id.document_name")
