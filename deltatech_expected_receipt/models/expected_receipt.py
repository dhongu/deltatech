# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Registrul încasărilor așteptate: bani încasați de la client care nu sunt încă în cont.

Cardul se încasează pe loc (plata 5125 = 4111 se scrie atunci), dar banca virează suma
grupată peste câteva zile. Rândul ține legătura dintre încasare și linia de extras care o
stinge, ca să nu se piardă pe drum și ca clientul să nu apară restant.
"""

import logging

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

_logger = logging.getLogger(__name__)

# Câte încasări intră cel mult în căutarea combinației.
MAX_CANDIDATES = 80
# Plafonul de memorie al căutării: masca păstrată după fiecare articol are câte un bit pe
# ban, deci 80 × 2.000.000 de biți ≈ 20 MB, eliberați după căutare.
MAX_TARGET_CENTS = 2_000_000
# Cronul de sincronizare: cât de în urmă se mai uită la rândurile decontate.
RESYNC_DAYS = 30
RESYNC_CHUNK = 200
# Banii de pe card intră de regulă în cel mult 3 zile.
DEFAULT_LATE_DAYS = 3

KINDS = [("card", "Card")]
STATES = [
    ("pending", "Pending Settlement"),
    ("settled", "Settled"),
    ("cancelled", "Cancelled"),
]
LIVE_STATES = ("pending", "settled")


class ExpectedReceipt(models.Model):
    _name = "deltatech.expected.receipt"
    _description = "Expected Receipt"
    _inherit = ["mail.thread"]
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(compute="_compute_name", store=True)
    kind = fields.Selection(KINDS, required=True, default="card", index=True, tracking=True)
    state = fields.Selection(STATES, required=True, default="pending", index=True, tracking=True, copy=False)
    partner_id = fields.Many2one("res.partner", "Customer", required=True, index=True, tracking=True)
    commercial_partner_id = fields.Many2one(
        "res.partner", related="partner_id.commercial_partner_id", store=True, index=True
    )
    sale_order_id = fields.Many2one(
        "sale.order", "Sales Order", index="btree_not_null", ondelete="set null", check_company=True, copy=False
    )
    invoice_id = fields.Many2one(
        "account.move",
        "Invoice",
        index="btree_not_null",
        ondelete="set null",
        check_company=True,
        copy=False,
        domain="[('move_type', 'in', ('out_invoice', 'out_refund'))]",
    )
    amount = fields.Monetary(required=True, tracking=True)
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id)
    date = fields.Date("Receipt Date", required=True, index=True, tracking=True, default=fields.Date.context_today)
    settlement_date = fields.Date(index="btree_not_null", copy=False, tracking=True)
    terminal_id = fields.Many2one(
        "deltatech.card.terminal", "Terminal", index="btree_not_null", check_company=True, tracking=True
    )
    user_id = fields.Many2one("res.users", "Received By", index=True, default=lambda self: self.env.user)
    payment_id = fields.Many2one(
        "account.payment", "Payment", index="btree_not_null", ondelete="set null", copy=False, check_company=True
    )
    statement_line_id = fields.Many2one(
        "account.bank.statement.line",
        "Statement Line",
        copy=False,
        index="btree_not_null",
        ondelete="set null",
        check_company=True,
        help="The grouped bank statement line that settled this receipt.",
    )
    company_id = fields.Many2one("res.company", required=True, index=True, default=lambda self: self.env.company)
    note = fields.Char()

    document_name = fields.Char("Document", compute="_compute_document_name")
    has_document = fields.Boolean(compute="_compute_has_document", store=True)
    days_pending = fields.Integer(compute="_compute_days_pending")
    is_late = fields.Boolean(
        "Late",
        compute="_compute_days_pending",
        search="_search_is_late",
        help="Not settled after the number of days set on the terminal.",
    )

    # ------------------------------------------------------------------
    @api.depends("kind", "partner_id", "date")
    def _compute_name(self):
        labels = dict(self._fields["kind"]._description_selection(self.env))
        for receipt in self:
            receipt.name = " · ".join(
                [
                    labels.get(receipt.kind, receipt.kind or ""),
                    receipt.partner_id.display_name or "—",
                    fields.Date.to_string(receipt.date) or "",
                ]
            )

    @api.depends("sale_order_id.name", "invoice_id.name")
    def _compute_document_name(self):
        for receipt in self:
            receipt.document_name = " · ".join(
                name for name in (receipt.invoice_id.name, receipt.sale_order_id.name) if name
            )

    @api.depends("sale_order_id", "invoice_id")
    def _compute_has_document(self):
        for receipt in self:
            receipt.has_document = bool(receipt.invoice_id or receipt.sale_order_id)

    @api.depends("date", "state", "terminal_id.late_days")
    def _compute_days_pending(self):
        today = fields.Date.context_today(self)
        for receipt in self:
            if receipt.state != "pending" or not receipt.date:
                receipt.days_pending = 0
                receipt.is_late = False
                continue
            receipt.days_pending = (today - receipt.date).days
            receipt.is_late = receipt.days_pending > receipt._late_days()

    def _late_days(self):
        self.ensure_one()
        return self.terminal_id.late_days if self.terminal_id else DEFAULT_LATE_DAYS

    @api.model
    def _search_is_late(self, operator, value):
        """Pragul e pe terminal, deci filtrul are câte o ramură pe fiecare prag distinct."""
        if operator != "in":
            return NotImplemented
        if True in value and False in value:
            return []
        today = fields.Date.context_today(self)
        terminals = self.env["deltatech.card.terminal"].with_context(active_test=False).search([])
        branches = []
        for days in sorted(set(terminals.mapped("late_days")) | {DEFAULT_LATE_DAYS}):
            limit = fields.Date.subtract(today, days=days)
            terminal_domain = [("terminal_id.late_days", "=", days)]
            if days == DEFAULT_LATE_DAYS:
                terminal_domain = ["|", ("terminal_id", "=", False), *terminal_domain]
            branches.append(["&", ("date", "<", limit), *terminal_domain])
        late_domain = ["|"] * (len(branches) - 1) + [term for branch in branches for term in branch]
        late_domain = ["&", ("state", "=", "pending"), *late_domain]
        return late_domain if True in value else ["!", *late_domain]

    # ------------------------------------------------------------------
    @api.constrains("amount", "currency_id")
    def _check_amount_positive(self):
        for receipt in self:
            if float_compare(receipt.amount, 0.0, precision_rounding=receipt.currency_id.rounding) <= 0:
                raise ValidationError(self.env._("The received amount must be greater than zero."))

    @api.constrains("kind", "state", "payment_id")
    def _check_card_has_payment(self):
        """Cardul se încasează pe loc, deci rândul are întotdeauna o plată.

        Fără regulă, cine are drept pe registru ar putea scrie „am încasat 8.000 lei cu
        cardul” fără nicio notă contabilă.
        """
        for receipt in self:
            if receipt.kind == "card" and receipt.state != "cancelled" and not receipt.payment_id:
                raise ValidationError(
                    self.env._(
                        "A card receipt is registered with the 'Card Payment' button, which also "
                        "creates the payment. A row without payment is not allowed."
                    )
                )

    @api.constrains("partner_id", "invoice_id", "sale_order_id")
    def _check_document_partner(self):
        for receipt in self:
            commercial = receipt.partner_id.commercial_partner_id
            for doc in (receipt.invoice_id, receipt.sale_order_id):
                if doc and doc.partner_id.commercial_partner_id != commercial:
                    raise ValidationError(
                        self.env._(
                            "Document %(doc)s belongs to %(other)s, not to %(partner)s.",
                            doc=doc.display_name,
                            other=doc.partner_id.commercial_partner_id.display_name,
                            partner=commercial.display_name,
                        )
                    )

    # Câmpurile care descriu banii: după ce există plata se schimbă doar prin butoanele
    # modulului (care fac și scrierea contabilă). Privilegiul e `sudo()`, nu o cheie de
    # context, pe care un client RPC o poate trimite oricând.
    MONEY_FIELDS = (
        "state",
        "amount",
        "currency_id",
        "date",
        "partner_id",
        "payment_id",
        "settlement_date",
        "statement_line_id",
        "kind",
        "invoice_id",
        "sale_order_id",
    )

    def write(self, vals):
        guarded = set(vals) & set(self.MONEY_FIELDS)
        if guarded and not self.env.su and not self.env.user.has_group("deltatech_expected_receipt.group_manager"):
            raise AccessError(
                self.env._("The amount and the state of a receipt change only through the register's buttons.")
            )
        return super().write(vals)

    def _check_manager(self):
        if not self.env.user.has_group("deltatech_expected_receipt.group_manager"):
            raise AccessError(self.env._("Only an expected receipts manager can do this."))

    # ------------------------------------------------------------------
    def action_open_document(self):
        self.ensure_one()
        record = self.invoice_id or self.sale_order_id
        if not record:
            raise UserError(self.env._("The receipt is on the customer's balance, without a document."))
        return {
            "type": "ir.actions.act_window",
            "res_model": record._name,
            "res_id": record.id,
            "views": [[False, "form"]],
        }

    def action_open_payment(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "res_id": self.payment_id.id,
            "views": [[False, "form"]],
        }

    def action_cancel(self):
        """Anulează încasarea (de exemplu tranzacția stornată pe terminal).

        Plata nereconciliată se anulează odată cu ea; una decontată nu se atinge, acolo
        banii au intrat și corecția e o stornare în contabilitate.
        """
        self._check_manager()
        for receipt in self:
            if receipt.state == "settled":
                raise UserError(
                    self.env._(
                        "The receipt of %s is already settled; reverse it in accounting.",
                        receipt.partner_id.display_name,
                    )
                )
            payment = receipt.payment_id
            if payment and payment.state not in ("canceled", "rejected"):
                if receipt._settlement_lines(include_reconciled=True).filtered("reconciled"):
                    raise UserError(
                        self.env._("Payment %s is already reconciled; unreconcile it first.", payment.display_name)
                    )
                # Nota plății rămâne, în starea anulată: numărul nu dispare din jurnal.
                payment.sudo().action_cancel()
            receipt.sudo().state = "cancelled"
            invoice = receipt.invoice_id
            if invoice and invoice.invoice_line_ids.sale_line_ids.filtered("is_downpayment"):
                # Factura de avans are TVA colectat: anularea plății n-o atinge.
                receipt.message_post(
                    body=self.env._(
                        "The down payment invoice %s stays posted: issue a credit note if the down "
                        "payment is not received.",
                        invoice.display_name,
                    ),
                    subtype_xmlid="mail.mt_note",
                )
        return True

    # ------------------------------------------------------------------
    def _settlement_lines(self, include_reconciled=False):
        """Liniile plăților de pe contul de decontare (5125): acestea le stinge extrasul."""
        lines = self.env["account.move.line"]
        for receipt in self:
            payment = receipt.payment_id
            if not payment or payment.move_id.state != "posted":
                continue
            lines |= payment.move_id.line_ids.filtered(
                lambda line, acc=payment.outstanding_account_id: line.account_id == acc
                and (include_reconciled or not line.reconciled)
            )
        return lines

    def _payment_is_reconciled(self):
        self.ensure_one()
        lines = self._settlement_lines(include_reconciled=True)
        return bool(lines) and all(lines.mapped("reconciled"))

    def _sync_state_from_accounting(self):
        """Aduce starea la ce spune contabilitatea, și când contabilul reconciliază din
        ecranul standard al Odoo, nu din ecranul de decontare."""
        for receipt in self:
            if receipt.state == "cancelled" or not receipt.payment_id:
                continue
            target = receipt.sudo()
            if receipt.payment_id.state in ("canceled", "rejected") and receipt.state != "settled":
                target.state = "cancelled"
                continue
            settled = receipt._payment_is_reconciled()
            if settled and receipt.state != "settled":
                target.write(
                    {
                        "state": "settled",
                        "settlement_date": receipt.settlement_date or receipt._guess_settlement_date(),
                    }
                )
            elif not settled and receipt.state == "settled":
                target.write({"state": "pending", "settlement_date": False, "statement_line_id": False})
        return True

    def _guess_settlement_date(self):
        self.ensure_one()
        dates = []
        for line in self._settlement_lines(include_reconciled=True):
            for partial in line.matched_debit_ids | line.matched_credit_ids:
                other = (partial.debit_move_id | partial.credit_move_id) - line
                dates += other.mapped("date")
        return max(dates) if dates else False

    @api.model
    def _cron_sync_settlements(self):
        cutoff = fields.Date.subtract(fields.Date.context_today(self), days=RESYNC_DAYS)
        receipts = self.sudo().search(
            [
                ("payment_id", "!=", False),
                "|",
                ("state", "=", "pending"),
                "&",
                ("state", "=", "settled"),
                ("settlement_date", ">=", cutoff),
            ]
        )
        for index in range(0, len(receipts), RESYNC_CHUNK):
            chunk = receipts[index : index + RESYNC_CHUNK]
            try:
                with self.env.cr.savepoint():
                    chunk._sync_state_from_accounting()
            except Exception:
                _logger.exception("Expected receipts: chunk %s could not be synchronized", chunk.ids)

    # ------------------------------------------------------------------
    #  Potrivirea combinației la decontare
    # ------------------------------------------------------------------
    @api.model
    def _candidates_for_statement(self, statement_line, terminal=None, window_days=4):
        """Încasările care pot intra în linia globală de extras: cele în așteptare, din
        fereastra T-window…T, pe jurnalul liniei, cele mai apropiate de extras primele."""
        start = fields.Date.subtract(statement_line.date, days=window_days)
        domain = [
            ("company_id", "=", statement_line.company_id.id),
            ("state", "=", "pending"),
            ("date", ">=", start),
            ("date", "<=", statement_line.date),
            ("currency_id", "=", statement_line.currency_id.id),
            ("payment_id.journal_id", "=", statement_line.journal_id.id),
        ]
        if terminal:
            domain.append(("terminal_id", "=", terminal.id))
        return self.search(domain, order="date desc, id desc", limit=MAX_CANDIDATES + 1)

    @api.model
    def _subset_sum(self, items, target_cents):
        """Subset-sum exact pe cenți, cu mulțimea sumelor atinse ținută ca biți.

        Bitul `s` al măștii e aprins dacă suma `s` (în bani) se poate face din articolele
        parcurse. Un articol de valoare `v` e o singură operație, `mask | (mask << v)`,
        făcută în C pe întregul mare: costul e liniar în „articole × țintă”, nu exponențial.
        Masca după fiecare articol permite reconstituirea combinației mergând înapoi.

        Întoarce indicii aleși sau `None`.
        """
        limit = (1 << (target_cents + 1)) - 1
        mask = 1
        prefixes = [mask]
        for value, _receipt in items:
            mask = (mask | (mask << value)) & limit
            prefixes.append(mask)
        if not (mask >> target_cents) & 1:
            return None
        chosen = []
        remaining = target_cents
        for index in range(len(items) - 1, -1, -1):
            if (prefixes[index] >> remaining) & 1:
                continue
            chosen.append(index)
            remaining -= items[index][0]
        return sorted(chosen)

    @api.model
    def _find_exact_combinations(self, receipts, target, currency, max_solutions=2):
        """Submulțimile de încasări care dau exact suma țintă, la ban, fără toleranță.

        Ambiguitatea se verifică prin excludere: pentru fiecare sumă distinctă din prima
        combinație se reia căutarea cu o copie mai puțin din acea sumă. Dacă tot iese ținta,
        există o combinație cu alt conținut. Două încasări egale de la clienți diferiți nu
        sunt raportate drept două soluții, iar ecranul nu alege niciodată între soluții.

        Întoarce `(soluții, motiv)`, cu motivul `too_many`, `too_complex`, `none`, `target`.
        """
        rounding = currency.rounding or 0.01
        if float_is_zero(target, precision_rounding=rounding) or target < 0:
            return [], "target"
        if len(receipts) > MAX_CANDIDATES:
            return [], "too_many"

        def cents(value):
            return int(round(value / rounding))

        target_c = cents(target)
        if target_c > MAX_TARGET_CENTS:
            return [], "too_complex"
        items = [(cents(receipt.amount), receipt) for receipt in receipts]
        items = [(value, receipt) for value, receipt in items if 0 < value <= target_c]
        if not items:
            return [], "none"
        first = self._subset_sum(items, target_c)
        if first is None:
            return [], "none"
        solutions = [self.browse([items[i][1].id for i in first])]
        first_values = [items[i][0] for i in first]
        for value in sorted(set(first_values)):
            if len(solutions) >= max_solutions:
                break
            keep = first_values.count(value) - 1
            reduced, used = [], 0
            for item_value, receipt in items:
                if item_value == value:
                    if used < keep:
                        used += 1
                        reduced.append((item_value, receipt))
                    continue
                reduced.append((item_value, receipt))
            other = self._subset_sum(reduced, target_c)
            if other is not None:
                solutions.append(self.browse([reduced[i][1].id for i in other]))
        return solutions, ""

    @api.model
    def _action_for_domain(self, domain):
        action = self.env["ir.actions.act_window"]._for_xml_id("deltatech_expected_receipt.action_expected_receipt")
        action["domain"] = domain
        action["context"] = {}
        return action
