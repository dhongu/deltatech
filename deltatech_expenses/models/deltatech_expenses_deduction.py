# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class DeltatechExpensesDeduction(models.Model):
    _name = "deltatech.expenses.deduction"
    _inherit = ["mail.thread"]
    _description = "Expenses Deduction"
    _order = "date_expense desc, id desc"
    _rec_name = "number"
    _check_company_auto = True

    @api.model
    def _default_journal(self):
        if self.env.context.get("default_journal_id", False):
            return self.env["account.journal"].browse(self.env.context.get("default_journal_id"))

        domain = [("type", "=", "cash"), ("company_id", "=", self.env.company.id)]
        return self.env["account.journal"].search(domain, limit=1)

    @api.model
    def _default_journal_diem(self):
        if self.env.context.get("default_journal_diem_id", False):
            return self.env["account.journal"].browse(self.env.context.get("default_journal_diem_id"))

        domain = [("type", "=", "general"), ("company_id", "=", self.env.company.id)]
        return self.env["account.journal"].search(domain, limit=1)

    @api.model
    def _default_account_diem(self):
        # `account.account` are `company_ids` (many2many) în O19, nu `company_id` — căutarea pe
        # `company_id` arunca ValueError, prins tăcut de un `except Exception` care mascase
        # complet eroarea; contul de diurnă implicit nu se completa niciodată automat (runda 2,
        # tichet POPVAL-COS).
        account_pool = self.env["account.account"]
        account_id = account_pool.search(
            [("code", "=ilike", "625%"), ("company_ids", "in", self.env.company.id)], limit=1
        )  # Cheltuieli cu deplasari
        if not account_id:
            account_id = account_pool.search(
                [("account_type", "=", "expense"), ("company_ids", "in", self.env.company.id)], limit=1
            )
        return account_id

    number = fields.Char(string="Number", size=32, readonly=True, default="/")
    state = fields.Selection(
        [("draft", "Draft"), ("advance", "Advance"), ("done", "Done"), ("cancel", "Cancelled")],
        string="Status",
        index=True,
        readonly=True,
        tracking=True,
        default="draft",
        copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed expenses deduction. \
            \n* The 'Done' status is set automatically when the expenses deduction is confirm.  \
            \n* The 'Cancelled' status is used when user cancel expenses deduction.",
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Aprobat de",
        readonly=True,
        copy=False,
        help="Utilizatorul care a validat avansul (rol Aprobator).",
    )
    accounted_by_id = fields.Many2one(
        "res.users",
        string="Contabilizat de",
        readonly=True,
        copy=False,
        help="Utilizatorul care a finalizat/contabilizat decontul (rol Contabil).",
    )
    date_expense = fields.Date(
        string="Expense Date",
        # readonly=True,
        # states={"draft": [("readonly", False)], "advance": [("readonly", False)]},
        index=True,
    )
    date_advance = fields.Date(
        string="Advance Date",
        required=True,
        # readonly=True,
        # states={"draft": [("readonly", False)]}
    )
    travel_order = fields.Char(
        string="Travel Order",
        # readonly=True,
        # states={"draft": [("readonly", False)]}
    )

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Employee Partner",
        related="employee_id.work_contact_id",
        store=True,
        help="Partenerul asociat angajatului (work_contact_id), folosit pentru notele contabile.",
    )

    expenses_line_ids = fields.One2many(
        "deltatech.expenses.deduction.line",
        "expenses_deduction_id",
        string="Expenses",
        # readonly=True,
        # states={"advance": [("readonly", False)]},
    )

    voucher_ids = fields.One2many(
        "account.move",
        "expenses_deduction_id",
        string="Vouchers",
        domain=[("move_type", "=", "in_receipt")],
        context={"default_move_type": "in_receipt"},
        # readonly=True,
        # states={"draft": [("readonly", False)]},
    )

    payment_ids = fields.One2many(
        "account.payment",
        "expenses_deduction_id",
        string="Payments",
        domain=[("payment_type", "=", "outbound")],
        context={"default_type": "outbound"},
        readonly=True,
    )

    note = fields.Text(string="Note")
    amount = fields.Monetary(string="Total Amount", compute="_compute_amount")
    amount_vouchers = fields.Monetary(string="Vouchers Amount", compute="_compute_amount")
    advance = fields.Monetary(
        string="Advance",
        readonly=True,
        # states={"draft": [("readonly", False)]}
    )

    difference = fields.Monetary(string="Difference", compute="_compute_amount")

    # Moneda decontului: a jurnalului de casă (casa în valută, 5314) sau a companiei. Avansul, liniile,
    # diurna și diferența sunt în această monedă; fiecare notă contabilă poartă suma în valută și
    # contravaloarea în moneda companiei la cursul BNR din data ei (OMFP 1802/2014 pct. 319).
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        compute="_compute_currency",
        store=True,
        readonly=False,
        precompute=True,
    )
    company_currency_id = fields.Many2one(related="company_id.currency_id", string="Company Currency")
    is_foreign_currency = fields.Boolean(compute="_compute_is_foreign_currency")

    # Cum ajung banii la angajat: din casă (cash), prin virament pe cardul lui personal (transfer)
    # sau deloc — cheltuielile se plătesc direct cu cardul firmei (company_card), fără avans pe 542.
    settlement_mode = fields.Selection(
        [("cash", "Cash"), ("transfer", "Bank transfer (personal card)"), ("company_card", "Company card")],
        string="Settlement Mode",
        required=True,
        default="cash",
        tracking=True,
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Payment Journal",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
        default=lambda self: self._default_journal(),
        check_company=True,
        help="Journal of the advance and of the difference: the cash journal, or the bank journal for a "
        "bank transfer to the personal card of the employee.",
    )
    card_journal_id = fields.Many2one(
        "account.journal",
        string="Company Card Journal",
        domain="[('type', 'in', ('bank', 'credit')), ('company_id', '=', company_id)]",
        check_company=True,
        help="Bank journal of the company card used by the employee: the receipts are settled on its "
        "outstanding payments account (5125), matched later with the bank statement.",
    )
    expense_journal_id = fields.Many2one("account.journal", string="Expense Journal")

    journal_diem_id = fields.Many2one(
        "account.journal",
        string="Diem Journal",
        default=lambda self: self._default_journal_diem(),
    )

    account_diem_id = fields.Many2one(
        "account.account",
        string="Diem Account",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)], "advance": [("readonly", False)]},
        default=lambda self: self._default_account_diem(),
    )

    move_id = fields.Many2one("account.move", string="Account Entry", readonly=True, copy=False)
    # move_ids = fields.One2many("account.move.line", related="move_id.line_ids", string="Journal Items", readonly=True)
    move_ids = fields.Many2many("account.move.line", string="Journal Items", readonly=True, compute="_compute_move_ids")

    diem = fields.Monetary(
        string="Diem",
        readonly=True,
        # states={"draft": [("readonly", False)], "advance": [("readonly", False)]},
        default=42.5,
    )
    # zecimal: diurna externă se acordă și pe fracțiuni de zi (50% până la 12 ore, HG 518/1995 art. 7^1)
    days = fields.Float(
        string="Days",
        digits=(16, 1),
        readonly=True,
        # states={"draft": [("readonly", False)], "advance": [("readonly", False)]},
    )

    total_diem = fields.Monetary(string="Total Diem", compute="_compute_amount")

    def _compute_move_ids(self):
        for expenses in self:
            move_lines = expenses.move_id.line_ids
            domain = [("expenses_deduction_id", "=", expenses.id)]
            moves = self.env["account.move"].search(domain)
            move_lines |= moves.mapped("line_ids")
            expenses.move_ids = move_lines

    @api.onchange("date_advance")
    def onchange_date_advance(self):
        if not self.date_expense or self.date_advance > self.date_expense:
            self.date_expense = self.date_advance

    @api.depends("expenses_line_ids", "days", "diem", "advance", "settlement_mode")
    def _compute_amount(self):
        for expense in self:
            total = 0.0
            for line in expense.expenses_line_ids:
                total += line.tax_amount + line.price_subtotal

            expense.amount_vouchers = total
            expense.total_diem = expense.days * expense.diem
            expense.amount = expense.amount_vouchers + expense.total_diem

            # cu cardul firmei chitanțele sunt plătite direct furnizorilor: angajatului i se datorează doar diurna
            owed = expense.total_diem if expense.settlement_mode == "company_card" else expense.amount
            expense.difference = owed - expense.advance

    @api.onchange("settlement_mode")
    def _onchange_settlement_mode(self):
        journal_type = "bank" if self.settlement_mode == "transfer" else "cash"
        if self.journal_id.type != journal_type:
            self.journal_id = self.env["account.journal"].search(
                [("type", "=", journal_type), ("company_id", "=", (self.company_id or self.env.company).id)], limit=1
            )
        if self.settlement_mode == "company_card":
            self.advance = 0.0
            if not self.card_journal_id:
                self.card_journal_id = self._employee_card_journal()

    @api.onchange("employee_id")
    def _onchange_employee_card(self):
        # mereu, și gol când noul angajat nu are card: altfel ar rămâne cardul angajatului precedent
        self.card_journal_id = self._employee_card_journal()

    def _employee_card_journal(self):
        """Jurnalul cardului de firmă de pe angajat: câmpul e vizibil doar contabilității, dar angajatul
        și aprobatorul își completează decontul, deci se citește cu sudo (doar valoarea jurnalului).
        Se propune doar dacă e al companiei decontului (check_company l-ar refuza abia la salvare)."""
        card_journal = self.employee_id.sudo().expenses_card_journal_id
        if card_journal.company_id != (self.company_id or self.env.company):
            return self.env["account.journal"]
        return card_journal.sudo(False)

    @api.depends("journal_id", "card_journal_id", "settlement_mode", "company_id")
    def _compute_currency(self):
        for expense in self:
            # cu cardul firmei chitanțele se decontează pe jurnalul cardului: moneda lui e moneda decontului
            journal = expense.card_journal_id if expense.settlement_mode == "company_card" else expense.journal_id
            expense.currency_id = journal.currency_id or expense.company_id.currency_id

    @api.depends("currency_id", "company_id")
    def _compute_is_foreign_currency(self):
        for expense in self:
            expense.is_foreign_currency = expense.currency_id != expense.company_id.currency_id

    def _to_company_currency(self, amount, date):
        """Contravaloarea în moneda companiei a unei sume în moneda decontului, la cursul BNR din `date`."""
        self.ensure_one()
        company = self.company_id or self.env.company
        if not self.currency_id or self.currency_id == company.currency_id:
            return amount
        return self.currency_id._convert(amount, company.currency_id, company, date or fields.Date.context_today(self))

    def _move_line_vals(self, amount, date, balance=None, **vals):
        """Valori pentru o linie de notă contabilă: `amount` e în moneda decontului (pozitiv = debit,
        negativ = credit); `balance` (moneda companiei) se calculează la cursul din `date` dacă lipsește."""
        self.ensure_one()
        if balance is None:
            balance = self._to_company_currency(amount, date)
        vals.update({"currency_id": self.currency_id.id, "amount_currency": amount, "balance": balance})
        return vals

    def _get_liquidity_account(self, journal, outbound=True):
        """Contul pe care ies (outbound) sau intră banii prin `journal`: contul casei, iar pentru un
        jurnal de bancă / card contul de plăți / încasări în curs al metodei de plată (5125), ca nota
        să se reconcilieze cu linia din extras — o notă direct pe 5121 s-ar dubla cu cea a extrasului."""
        self.ensure_one()
        if journal.type == "cash":
            return journal.default_account_id
        method_lines = journal.outbound_payment_method_line_ids if outbound else journal.inbound_payment_method_line_ids
        account = method_lines.payment_account_id[:1]
        if not account:
            raise UserError(
                self.env._(
                    "Set an outstanding %(direction)s account (5125) on the %(direction)s payment method of the "
                    "journal %(journal)s: the payments of the expenses deduction %(number)s are posted on it and "
                    "matched with the bank statement.",
                    direction=self.env._("payments") if outbound else self.env._("receipts"),
                    journal=journal.display_name,
                    number=self.number,
                )
            )
        return account

    def _check_settlement_mode(self):
        for expenses in self:
            mode = expenses.settlement_mode
            for journal in expenses.journal_id | expenses.card_journal_id:
                # un jurnal în valută (cont 5314 / 5124) primește doar note în moneda lui
                if journal.currency_id and journal.currency_id != expenses.currency_id:
                    raise UserError(
                        self.env._(
                            "The journal %(journal)s is in %(journal_currency)s, but the expenses deduction "
                            "%(number)s is in %(currency)s.",
                            journal=journal.display_name,
                            journal_currency=journal.currency_id.name,
                            number=expenses.number,
                            currency=expenses.currency_id.name,
                        )
                    )
            if mode == "cash" and expenses.journal_id.type != "cash":
                raise UserError(
                    self.env._(
                        "The expenses deduction %(number)s is settled in cash: choose a cash journal.",
                        number=expenses.number,
                    )
                )
            if mode == "transfer" and expenses.journal_id.type not in ("bank", "credit"):
                raise UserError(
                    self.env._(
                        "The expenses deduction %(number)s is settled by bank transfer: choose a bank journal.",
                        number=expenses.number,
                    )
                )
            if mode == "company_card":
                if expenses.card_journal_id.type not in ("bank", "credit"):
                    raise UserError(
                        self.env._(
                            "The expenses deduction %(number)s is paid with a company card: choose the company "
                            "card journal (a bank or credit card journal).",
                            number=expenses.number,
                        )
                    )
                if expenses.advance:
                    raise UserError(
                        self.env._(
                            "The expenses deduction %(number)s is paid with a company card: it has no advance. "
                            "A cash withdrawal with the card is a separate deduction (Dr 542 = Cr 5121).",
                            number=expenses.number,
                        )
                    )

    def _check_role(self, group_xmlid, action):
        """Verificare explicită de rol pentru acțiunile ireversibile/contabile: dreptul de scriere
        pe model (necesar oricărui utilizator din cele 3 grupuri) nu separă singur angajat de
        aprobator/contabil, fiindcă metodele de mai jos scriu pe același model. (tichet POPVAL-COS)
        Modul superuser (sudo/migrări/scripturi tehnice) ocolește verificarea, ca orice altă
        regulă de acces din Odoo."""
        if self.env.su:
            return
        if not self.env.user.has_group(group_xmlid):
            raise AccessError(self.env._("Nu aveți rolul necesar pentru a %s decontul de cheltuieli.") % (action,))

    # Câmpuri scrise doar de metodele de flux (validate_advance / validate_expenses /
    # invalidate_expenses / cancel_expenses), care verifică rolul și scriu în sudo.
    _WORKFLOW_FIELDS = ("state", "approved_by_id", "accounted_by_id", "move_id")
    # Stările în care decontul e închis: sumele și notele contabile nu se mai modifică prin write.
    _LOCKED_STATES = ("done", "cancel")

    def _get_locked_fields(self):
        """Câmpurile care intră în sume, linii sau note contabile și care nu se mai modifică pe un
        decont Finalizat/Anulat. Modulele care adaugă câmpuri cu efect contabil le adaugă aici."""
        return {
            "number",
            "company_id",
            "currency_id",
            "employee_id",
            "date_advance",
            "date_expense",
            "settlement_mode",
            "journal_id",
            "card_journal_id",
            "expense_journal_id",
            "journal_diem_id",
            "account_diem_id",
            "advance",
            "diem",
            "days",
            "expenses_line_ids",
            "voucher_ids",
            "payment_ids",
        }

    def _get_advance_locked_fields(self):
        """Câmpurile care au intrat în nota de avans (Dr 542 = Cr casă) postată la „Avans”: nu se mai
        modifică în starea Avans, altfel diferența de la decontare se calculează față de alt avans
        decât cel din registru (restituire fictivă, sold creditor pe 542)."""
        return {
            "advance",
            "settlement_mode",
            "journal_id",
            "card_journal_id",
            "expense_journal_id",
            "date_advance",
            "employee_id",
            "company_id",
            "currency_id",
        }

    def _check_workflow_write(self, vals):
        """EXPENSES-001: starea și câmpurile de flux se schimbă doar prin metodele de flux, iar un
        decont Finalizat/Anulat nu își mai schimbă sumele, liniile sau notele. Superuserul (sudo,
        migrări, metodele de flux după verificarea rolului) nu este blocat."""
        if self.env.su:
            return

        def _changes(rec, fname):
            current = rec[fname]
            current = current.id if isinstance(current, models.BaseModel) else current
            return (current or False) != (vals[fname] or False)

        if any(_changes(rec, fname) for fname in self._WORKFLOW_FIELDS if fname in vals for rec in self):
            raise UserError(
                self.env._(
                    "The status of an expenses deduction is changed only with the workflow buttons "
                    "(Advance, Validate, Invalidate), not by a direct write."
                )
            )
        locked = self._get_locked_fields() & set(vals)
        if locked:
            closed = self.filtered(lambda rec: rec.state in self._LOCKED_STATES)
            if closed:
                raise UserError(
                    self.env._(
                        "The expenses deduction %(number)s is done or cancelled: its amounts, lines and "
                        "accounting data can no longer be changed. Invalidate it and validate it again.",
                        number=closed[0].number,
                    )
                )
        if self._get_advance_locked_fields() & set(vals):
            advanced = self.filtered(lambda rec: rec.state == "advance")
            if advanced:
                raise UserError(
                    self.env._(
                        "The advance of the expenses deduction %(number)s is already posted: the advance amount, "
                        "journals, advance date, employee and company can no longer be changed. To change the "
                        "advance, invalidate the deduction.",
                        number=advanced[0].number,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            for vals in vals_list:
                if vals.get("state", "draft") != "draft" or any(
                    vals.get(fname) for fname in self._WORKFLOW_FIELDS if fname != "state"
                ):
                    raise UserError(
                        self.env._(
                            "An expenses deduction is created in the Draft status; the status is changed "
                            "only with the workflow buttons."
                        )
                    )
        return super().create(vals_list)

    def write(self, vals):
        self._check_workflow_write(vals)
        return super().write(vals)

    def unlink(self):
        self._check_role("deltatech_expenses.group_expenses_accounting", "șterge")
        for t in self:
            if t.state not in ("draft", "cancel"):
                raise UserError(self.env._("Cannot delete Expenses Deduction(s) which are already done."))
        return super().unlink()

    def invalidate_expenses(self):
        self._check_role("deltatech_expenses.group_expenses_accounting", "invalida")
        for expenses in self:
            if expenses.state != "done":
                raise UserError(
                    self.env._("Decontul %s nu poate fi invalidat: nu este în starea Finalizat.") % (expenses.number,)
                )
        # vezi validate_advance: contabilizarea (aici, anularea ei) rulează cu drepturi complete
        # odată ce rolul de Contabil a fost verificat mai sus.
        self = self.sudo()
        moves = self.env["account.move"]
        for expenses in self:
            if expenses.move_id:
                moves |= expenses.move_id
            domain = [("expenses_deduction_id", "=", expenses.id)]
            moves |= self.env["account.move"].search(domain)

        self.write({"state": "draft", "move_id": False})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            for move in moves:
                move.line_ids.remove_move_reconcile()
            moves.with_context(force_delete=True).unlink()

        # anulare plati inregistrate
        for expenses in self:
            expenses.voucher_ids.button_cancel()

            # expenses.payment_ids.cancel_voucher()
            # expenses.payment_ids.cancel()
            expenses.payment_ids.action_draft()
            expenses.payment_ids.action_cancel()
            # domain = [('voucher_id', 'in', expenses.payment_ids.ids)]
            # statement_lines = self.env['account.bank.statement.line'].search(domain)
            # if statement_lines:
            #     statement_lines.unlink()
            # expenses.payment_ids.write({"move_name": False, "state": "draft"})
            expenses.payment_ids.with_context(force_delete=True).unlink()
            expenses.voucher_ids.with_context(force_delete=True).unlink()

            # anulare postare chitante.

            # eliberăm liniile provenite din surse externe (ex. hr.expense, via
            # deltatech_expenses_hr_expense); liniile introduse manual rămân pentru re-validare.
            expenses._release_imported_lines()

        # todo: de facut cancel dupa expenses_line_ids
        # for expenses in self:
        #    expenses.line_ids.cancel_voucher()
        #    expenses.line_ids.action_cancel_draft()

        # statement_lines = self.env["account.bank.statement.line"].search([("expenses_deduction_id", "=", expenses.id)])
        # if statement_lines:
        #     statement_lines.unlink()

        return True

    def _release_imported_lines(self):
        """Hook de extensie: modulele care preiau cheltuieli din alte surse (ex. hr.expense, via
        deltatech_expenses_hr_expense) elimină aici, la invalidare, liniile provenite din acea sursă."""
        return

    def validate_advance(self):
        self._check_role("deltatech_expenses.group_expenses_approver", "aproba avansul pentru")
        for expenses in self:
            if expenses.state != "draft":
                raise UserError(
                    self.env._(
                        "Decontul %s nu poate fi validat ca avans: nu mai este în starea Ciornă "
                        "(a fost deja validat sau invalidat)."
                    )
                    % (expenses.number,)
                )
        # Odată rolul verificat mai sus, contabilizarea propriu-zisă rulează cu drepturi complete:
        # un Aprobator nu trebuie să aibă și grupurile standard de Contabilitate/Jurnale doar ca
        # să poată apăsa acest buton (tichet POPVAL-COS, pct. 6).
        self = self.sudo()
        self._check_settlement_mode()
        for expenses in self:
            if not expenses.number or expenses.number == "/":
                sequence = self.env.ref("deltatech_expenses.sequence_expenses_deduction")
                name = sequence.next_by_id()
                expenses.write({"number": name})
            else:
                name = expenses.number

            if expenses.advance:
                account = expenses.expense_journal_id.default_account_id
                # statement = self.get_statement(expenses.date_advance)
                # values = {
                #     "amount": -expenses.advance,
                #     "date": expenses.date_advance,
                #     "partner_id": expenses.partner_id.id,
                #     "statement_id": statement.id,
                #     "journal_id": expenses.journal_id.id,
                #     "ref": expenses.number,
                #     "expenses_deduction_id": expenses.id,
                #     "payment_ref": "Avans",
                #     "counterpart_account_id": account.id,
                #     "backup_counterpart_account_id": account.id,
                # }
                # self.env["account.bank.statement.line"].with_context(counterpart_account_id=account.id).create(values)
                value = {
                    "journal_id": expenses.journal_id.id,
                    "date": expenses.date_advance,
                    "ref": expenses.number,
                    "expenses_deduction_id": expenses.id,
                }
                advance_balance = expenses._to_company_currency(expenses.advance, expenses.date_advance)
                value_lines = [
                    expenses._move_line_vals(
                        expenses.advance,
                        expenses.date_advance,
                        advance_balance,
                        partner_id=expenses.partner_id.id,
                        account_id=account.id,
                        name=self.env._("Avans"),
                    ),
                    expenses._move_line_vals(
                        -expenses.advance,
                        expenses.date_advance,
                        -advance_balance,
                        partner_id=expenses.partner_id.id,
                        account_id=expenses._get_liquidity_account(expenses.journal_id).id,
                        name=self.env._("Avans"),
                    ),
                ]
                value["line_ids"] = [(0, 0, x) for x in value_lines]
                move = self.env["account.move"].create(value)
                move._post()

            expenses.write({"state": "advance", "number": name, "approved_by_id": self.env.user.id})

    def _create_advance_settlement(self, expenses, partner, amount, date, ref, payable_account=None, balance=None):
        """Notă de decontare a cheltuielii din avans: Dr cont furnizor (401, partenerul furnizor)
        = Cr 542 (partenerul angajatului — avansul rămâne închis pe cine l-a primit).

        Plătită cu cardul firmei, cheltuiala nu trece prin 542: Dr 401 = Cr 5125 (plăți în curs ale
        jurnalului cardului, partenerul furnizor), închis la importul extrasului cu 5125 = 5121.

        `amount` e în moneda decontului; `balance` (moneda companiei) se dă când trebuie să fie
        exact cel al datoriei decontate (linia furnizor a chitanței), altfel se calculează la cursul decontului.

        În Odoo 19 nu se folosește `account.payment` pentru această operațiune: jurnalul de avans
        este de tip „general" (fără metode de plată), iar o plată pe casă ar dubla mișcarea de
        numerar (avansul a ieșit deja din casă). Nota se reconciliază cu chitanța de achiziție.
        """
        if not payable_account:
            payable_account = partner.with_company(expenses.company_id).property_account_payable_id
        if not payable_account:
            raise UserError(
                self.env._(
                    "Furnizorul %s nu are un cont de datorii (401) configurat; "
                    "completați 'Cont de plătit' pe partener înainte de decontare."
                )
                % (partner.display_name or "")
            )
        if expenses.settlement_mode == "company_card":
            credit_journal = expenses.card_journal_id
            credit_account = expenses._get_liquidity_account(credit_journal)
            credit_partner = partner
        else:
            credit_journal = expenses.expense_journal_id
            credit_account = expenses.expense_journal_id.default_account_id  # 542
            credit_partner = expenses.partner_id
        date = date or expenses.date_expense
        if balance is None:
            balance = expenses._to_company_currency(amount, date)
        move = self.env["account.move"].create(
            {
                "journal_id": credit_journal.id,
                "date": date,
                "ref": ref,
                "expenses_deduction_id": expenses.id,
                "line_ids": [
                    (
                        0,
                        0,
                        expenses._move_line_vals(
                            amount,
                            date,
                            balance,
                            partner_id=partner.id,
                            account_id=payable_account.id,
                            name=self.env._("Decontare avans"),
                        ),
                    ),
                    (
                        0,
                        0,
                        # partenerul angajatului, NU furnizorul: 542 trebuie să rămână analitic
                        # pe cine a primit avansul, altfel soldul analitic per partener e greșit
                        # deși contul se închide global (vezi tichet POPVAL-COS).
                        expenses._move_line_vals(
                            -amount,
                            date,
                            -balance,
                            partner_id=credit_partner.id,
                            account_id=credit_account.id,
                            name=self.env._("Decontare avans"),
                        ),
                    ),
                ],
            }
        )
        move._post()
        return move

    def _reconcile_supplier_payment(self, settle_payable):
        """Reconciliază linia de furnizor a unei plăți directe (supplier_payment) cu datoriile
        deschise ale aceluiași furnizor pe același cont (ca o plată: stinge facturile existente).
        Ce rămâne neacoperit de datorii deschise e un avans acordat furnizorului și se trece pe
        4092 (vezi _reclassify_supplier_advance)."""
        settle_payable.ensure_one()
        open_lines = self.env["account.move.line"].search(
            [
                ("partner_id", "=", settle_payable.partner_id.id),
                ("account_id", "=", settle_payable.account_id.id),
                # restrâns la aceeași companie: fără acest filtru, o plată din avans putea stinge
                # o datorie a aceluiași furnizor înregistrată în altă companie (tichet POPVAL-COS).
                ("company_id", "=", settle_payable.company_id.id),
                ("parent_state", "=", "posted"),
                ("reconciled", "=", False),
                ("balance", "<", 0.0),  # datorii deschise (credit furnizor)
                ("id", "!=", settle_payable.id),
            ]
        )
        if open_lines:
            (settle_payable | open_lines).reconcile()
        self._reclassify_supplier_advance(settle_payable)

    def _reclassify_supplier_advance(self, settle_payable):
        """Soldul debitor rămas pe 401 după o plată directă din avans este un avans acordat
        furnizorului: Dr 4092 = Cr 401, reconciliat cu plata. Conform funcțiunii conturilor
        (OMFP 1802/2014), 409 se debitează prin 401, nu direct prin 542. La primirea facturii,
        avansul se regularizează Dr 401 = Cr 4092. Fără cont 4092 în plan, soldul rămâne pe 401."""
        residual = settle_payable.amount_residual
        if settle_payable.company_currency_id.is_zero(residual) or residual < 0:
            return
        currency = settle_payable.currency_id
        residual_currency = settle_payable.amount_residual_currency
        account_409 = self.env["account.account"].search(
            [("code", "=like", "4092%"), ("company_ids", "in", settle_payable.company_id.id)], limit=1
        )
        if not account_409:
            return
        move = self.env["account.move"].create(
            {
                "journal_id": settle_payable.journal_id.id,
                "date": settle_payable.date,
                "ref": settle_payable.move_id.ref,
                "expenses_deduction_id": settle_payable.move_id.expenses_deduction_id.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": settle_payable.partner_id.id,
                            "account_id": account_409.id,
                            "name": self.env._("Avans furnizor"),
                            "currency_id": currency.id,
                            "amount_currency": residual_currency,
                            "balance": residual,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "partner_id": settle_payable.partner_id.id,
                            "account_id": settle_payable.account_id.id,
                            "name": self.env._("Avans furnizor"),
                            "currency_id": currency.id,
                            "amount_currency": -residual_currency,
                            "balance": -residual,
                        },
                    ),
                ],
            }
        )
        move._post()
        (settle_payable | move.line_ids.filtered(lambda aml: aml.account_id == settle_payable.account_id)).reconcile()

    def validate_expenses(self):
        # poate ar fi bine daca  bonurile fiscale de la acelasi furnizor sa fie unuite intr-o singura chitanta.

        self._check_role("deltatech_expenses.group_expenses_accounting", "finaliza (contabiliza)")
        for expenses in self:
            if expenses.state != "advance":
                raise UserError(
                    self.env._(
                        "Decontul %s nu poate fi validat: nu este în starea Avans "
                        "(a fost deja finalizat sau nu are un avans validat)."
                    )
                    % (expenses.number,)
                )

        # Odată rolul verificat mai sus, contabilizarea propriu-zisă rulează cu drepturi complete
        # (vezi validate_advance) — un Contabil nu trebuie să mai aibă și acces direct pe jurnale
        # doar ca să poată finaliza decontul (tichet POPVAL-COS, pct. 6).
        self = self.sudo()
        self._check_settlement_mode()

        domain = [
            ("type", "=", "purchase"),
            ("company_id", "=", self.company_id.id),
        ]
        purchase_journal = self.env["account.journal"].search(domain, limit=1)
        partner_generic = self.company_id.generic_partner_id
        if not partner_generic:
            partner_generic = self.env.ref("deltatech_partner_generic.partner_generic", raise_if_not_found=False)

        for expenses in self:
            name = expenses.number
            expenses_vals = {"state": "done", "number": name, "accounted_by_id": self.env.user.id}
            vouchers = self.env["account.move"]

            # reconcile = self.env['account.full.reconcile'].create({'name':name})

            for line in expenses.expenses_line_ids:
                partner_id = line.partner_id or partner_generic
                if not partner_id:
                    raise UserError(self.env._("You must select a supplier for all lines."))
                if line.type == "expenses":
                    # Chitanța recalculează taxa din price_unit (compute_all). Pentru taxe „TVA
                    # inclus în preț" trebuie trimis brutul (line.amount) — trimiterea netului
                    # (price_subtotal) ar extrage TVA a doua oară, subevaluând baza, TVA-ul
                    # deductibil și totalul documentului (tichet POPVAL-COS). Pentru taxe „pe
                    # deasupra" se trimite baza extrasă din brut (price_subtotal).
                    line_price_include = bool(line.tax_ids) and all(line.tax_ids.mapped("price_include"))
                    line_price_unit = line.amount if line_price_include else line.price_subtotal
                    voucher_value = {
                        "partner_id": partner_id.id,
                        "move_type": "in_receipt",
                        # "pay_now": "pay_now",
                        "invoice_date": line.date,
                        "date": line.date,
                        "ref": line.name,
                        "journal_id": purchase_journal.id,
                        # chitanța e în moneda decontului; Odoo o convertește la cursul din data ei
                        "currency_id": expenses.currency_id.id,
                        # "payment_journal_id": expenses.journal_payment_id.id,  # plata prin jurnalu de decont chelturili
                        "expenses_deduction_id": expenses.id,
                        # 'account_id': expenses.journal_payment_id.default_debit_account_id.id,  # 542
                        # "account_id": partner_id.property_account_receivable_id.id,
                        # aici trebuie sa fie contul din care se face plata furnizorului
                        "invoice_line_ids": [
                            (
                                0,
                                0,
                                {
                                    "name": line.name,
                                    "price_unit": line_price_unit,
                                    "tax_ids": [(6, 0, line.tax_ids.ids)],
                                    "account_id": line.expense_account_id.id,
                                    "analytic_distribution": line.analytic_distribution,
                                },
                            )
                        ],
                    }
                    vouchers |= self.env["account.move"].create(voucher_value)
                else:
                    # plată directă către furnizor din avans (fără chitanță): Dr 401 = Cr 542,
                    # apoi se reconciliază cu datoriile deschise ale furnizorului (ca o plată)
                    settle = self._create_advance_settlement(
                        expenses, partner_id, line.tax_amount + line.price_subtotal, line.date, name
                    )
                    settle_payable = settle.line_ids.filtered(
                        lambda aml: aml.account_id.account_type == "liability_payable"
                    )
                    self._reconcile_supplier_payment(settle_payable)

            vouchers.action_post()

            # Decontarea cheltuielilor: pentru fiecare chitanță, notă directă Dr 401 = Cr 542,
            # reconciliată cu linia furnizor a chitanței (închide datoria către furnizor din avans).
            for voucher in vouchers:
                for payable in voucher.line_ids.filtered(
                    lambda aml: aml.account_id.account_type == "liability_payable"
                ):
                    # aceleași sume (valută și lei) ca datoria chitanței, ca reconcilierea să o închidă complet
                    settle = self._create_advance_settlement(
                        expenses,
                        payable.partner_id,
                        -payable.amount_currency,
                        voucher.date,
                        name,
                        payable_account=payable.account_id,
                        balance=-payable.balance,
                    )
                    settle_payable = settle.line_ids.filtered(lambda aml: aml.account_id == payable.account_id)
                    (payable | settle_payable).reconcile()

            # payment_state se calculează automat de Odoo din reconciliere (chitanța e in_receipt,
            # deci intră în is_invoice(include_receipts=True)) — nu-l mai forțăm manual (runda 2,
            # tichet POPVAL-COS: scrierea directă a payment_state ocolea calculul standard).

            account_542 = expenses.expense_journal_id.default_account_id
            date_expense = expenses.date_expense or fields.Date.context_today(self)
            if expenses.difference:
                # difference < 0: restituire (Dr casă / 5125 încasări în curs = Cr 542);
                # > 0: plată suplimentară (Dr 542 = Cr casă / 5125 plăți în curs)
                value_lines = [
                    expenses._move_line_vals(
                        expenses.difference,
                        date_expense,
                        partner_id=expenses.partner_id.id,
                        account_id=account_542.id,
                        name=self.env._("Diferență avans"),
                    ),
                    expenses._move_line_vals(
                        -expenses.difference,
                        date_expense,
                        partner_id=expenses.partner_id.id,
                        account_id=expenses._get_liquidity_account(
                            expenses.journal_id, outbound=expenses.difference > 0
                        ).id,
                        name=self.env._("Diferență avans"),
                    ),
                ]
                value = {
                    "journal_id": expenses.journal_id.id,
                    # restituirea/plata diferenței are loc la decontare, nu la acordarea avansului
                    "date": date_expense,
                    "ref": expenses.number,
                    "expenses_deduction_id": expenses.id,
                }

                value["line_ids"] = [(0, 0, x) for x in value_lines]
                move = self.env["account.move"].create(value)
                move._post()

            if expenses.total_diem:
                common = {
                    "name": self.env._("Diurnă"),
                    "partner_id": expenses.partner_id.id,
                    "date_maturity": date_expense,
                }
                diem_balance = expenses._to_company_currency(expenses.total_diem, date_expense)
                line_ids = [
                    (
                        0,
                        0,
                        expenses._move_line_vals(
                            expenses.total_diem,
                            date_expense,
                            diem_balance,
                            account_id=expenses.account_diem_id.id,
                            **common,
                        ),
                    ),
                    (
                        0,
                        0,
                        expenses._move_line_vals(
                            -expenses.total_diem,
                            date_expense,
                            -diem_balance,
                            account_id=account_542.id,
                            **common,
                        ),
                    ),
                ]
                move = self.env["account.move"].create(
                    {
                        # "name": name or "/",
                        "journal_id": expenses.journal_diem_id.id,
                        "date": date_expense,
                        "ref": name or "",
                        "line_ids": line_ids,
                    }
                )
                expenses_vals["move_id"] = move.id
                move.action_post()

            expenses._close_542_exchange_difference(date_expense, expenses_vals.get("move_id"))

            expenses.write(expenses_vals)

    def _close_542_exchange_difference(self, date, diem_move_id=False):
        """Decont în valută: avansul, cheltuielile, diurna și diferența sunt fiecare la cursul BNR din
        data lor (OMFP 1802/2014 pct. 319), deci 542 se închide în valută, dar poate rămâne un sold în
        lei. Acesta e diferența de curs la decontare (pct. 322, funcțiunea contului 542):
        Dr 665 = Cr 542 (nefavorabilă) sau Dr 542 = Cr 765 (favorabilă)."""
        self.ensure_one()
        company = self.company_id
        if not self.is_foreign_currency:
            return
        account_542 = self.expense_journal_id.default_account_id
        domain = [
            ("account_id", "=", account_542.id),
            ("parent_state", "=", "posted"),
            "|",
            ("move_id.expenses_deduction_id", "=", self.id),
            ("move_id", "=", diem_move_id or 0),
        ]
        lines_542 = self.env["account.move.line"].search(domain)
        residual = company.currency_id.round(sum(lines_542.mapped("balance")))
        if company.currency_id.is_zero(residual):
            return
        if residual > 0:
            exchange_account = company.expense_currency_exchange_account_id
        else:
            exchange_account = company.income_currency_exchange_account_id
        if not exchange_account:
            raise UserError(
                self.env._(
                    "Set the gain and loss exchange rate accounts (765/665) in the accounting settings of "
                    "the company %(company)s, to close the exchange difference of the expenses deduction %(number)s.",
                    company=company.name,
                    number=self.number,
                )
            )
        common = {"partner_id": self.partner_id.id, "name": self.env._("Diferență de curs avans")}
        move = self.env["account.move"].create(
            {
                "journal_id": (company.currency_exchange_journal_id or self.expense_journal_id).id,
                "date": date,
                "ref": self.number,
                "expenses_deduction_id": self.id,
                "line_ids": [
                    (0, 0, self._move_line_vals(0.0, date, residual, account_id=exchange_account.id, **common)),
                    (0, 0, self._move_line_vals(0.0, date, -residual, account_id=account_542.id, **common)),
                ],
            }
        )
        move._post()
        return move

    # def get_statement(self, date):
    #     statement = self.env["account.bank.statement"].search(
    #         [("journal_id", "=", self.journal_id.id), ("date", "=", date)], limit=1
    #     )
    #     if not statement:
    #         vals = {
    #             "journal_id": self.journal_id.id,
    #             # "state": "open",
    #             "date": date,
    #         }
    #         statement = self.env["account.bank.statement"].create(vals)
    #
    #     # if statement.state != "open":
    #     #     raise UserError(
    #     #         _(
    #     #             "The cash statement of journal %s from date is not in open state, please open it \n"
    #     #             'to create the line in  it "%s".'
    #     #         )
    #     #         % (self.journal_id.name, date)
    #     #     )
    #     return statement

    def cancel_expenses(self):
        self._check_role("deltatech_expenses.group_expenses_accounting", "anula")
        for expenses in self:
            if expenses.state != "draft":
                # din Avans/Finalizat există note contabile postate: anularea le-ar lăsa în urmă
                raise UserError(
                    self.env._(
                        "The expenses deduction %(number)s cannot be cancelled: only a draft deduction can "
                        "be cancelled (an advanced or done one has journal entries).",
                        number=expenses.number,
                    )
                )
        self.sudo().write({"state": "cancel"})
        return True


class DeltatechExpensesDeductionLine(models.Model):
    _name = "deltatech.expenses.deduction.line"
    _inherit = "analytic.mixin"
    _description = "Expenses Deduction Line"

    @api.model
    def _default_expense_account(self):
        account_pool = self.env["account.account"]
        company_domain = [("company_ids", "in", self.env.company.id)]
        account = account_pool.search([("code", "=ilike", "623%")] + company_domain, limit=1)  # protocol
        if not account:
            account = account_pool.search([("account_type", "=", "expense")] + company_domain, limit=1)
        return account

    expenses_deduction_id = fields.Many2one("deltatech.expenses.deduction", string="Expenses Deduction", required=False)
    date = fields.Date("Date", index=True, copy=False, default=fields.Date.context_today)
    name = fields.Text(string="Reference", required=True)
    tax_ids = fields.Many2many(
        "account.tax", string="Tax", help="VAT on the receipt; the amount is always entered with VAT included."
    )

    type = fields.Selection([("expenses", "Expenses"), ("supplier_payment", "Supplier Payment")], default="expenses")

    # Suma de pe bon/factură, mereu cu TVA inclus, indiferent dacă taxa e configurată „inclusă
    # în preț" sau „pe deasupra" (taxele RO standard de achiziție sunt pe deasupra).
    amount = fields.Monetary(string="Total", help="Amount on the receipt, VAT included.")
    tax_amount = fields.Monetary(readonly=True, store=True, compute="_compute_subtotal")
    price_subtotal = fields.Monetary(readonly=True, store=True, compute="_compute_subtotal")  # valoare subtotal

    # todo: de scos required si de acompletat cu partner_generic in situatia in care nu se completeaza nimic
    partner_id = fields.Many2one("res.partner", string="Partner")
    # The line currency is always the currency of the deduction (company currency or the currency of
    # a foreign currency cash journal), never an independent value: line amounts are added to the
    # advance and posted in the same currency.
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        compute="_compute_currency_id",
        store=True,
        precompute=True,
    )

    expense_account_id = fields.Many2one(
        "account.account", default=lambda self: self._default_expense_account(), string="Default Expense Account"
    )

    state = fields.Selection(related="expenses_deduction_id.state")

    @api.depends("expenses_deduction_id.currency_id", "expenses_deduction_id.company_id")
    def _compute_currency_id(self):
        for line in self:
            deduction = line.expenses_deduction_id
            line.currency_id = deduction.currency_id or (deduction.company_id or self.env.company).currency_id

    def _check_deduction_open(self, deductions):
        """EXPENSES-001: liniile unui decont Finalizat/Anulat nu se mai creează, modifică sau
        șterg (ar schimba totalurile față de chitanțele și notele deja postate)."""
        if self.env.su:
            return
        closed = deductions.filtered(lambda d: d.state in self.env["deltatech.expenses.deduction"]._LOCKED_STATES)
        if closed:
            raise UserError(
                self.env._(
                    "The expenses deduction %(number)s is done or cancelled: its lines can no longer "
                    "be changed. Invalidate it and validate it again.",
                    number=closed[0].number,
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        # the currency is derived from the deduction, a value sent by the caller is ignored
        for vals in vals_list:
            vals.pop("currency_id", None)
        deduction_ids = [vals["expenses_deduction_id"] for vals in vals_list if vals.get("expenses_deduction_id")]
        self._check_deduction_open(self.env["deltatech.expenses.deduction"].browse(deduction_ids))
        return super().create(vals_list)

    def write(self, vals):
        if "currency_id" in vals:
            vals = dict(vals)
            vals.pop("currency_id")
        deductions = self.mapped("expenses_deduction_id")
        if vals.get("expenses_deduction_id"):
            deductions |= self.env["deltatech.expenses.deduction"].browse(vals["expenses_deduction_id"])
        self._check_deduction_open(deductions)
        return super().write(vals)

    def unlink(self):
        self._check_deduction_open(self.mapped("expenses_deduction_id"))
        return super().unlink()

    @api.model
    def _get_company(self):
        return self.env.context.get("company_id", self.env.user.company_id.id)

    @api.depends("amount", "tax_ids")
    def _compute_subtotal(self):
        for expenses in self:
            tax_amount = 0.0
            price_subtotal = expenses.amount
            taxes = expenses.tax_ids
            if taxes:
                price_unit = expenses.amount
                if not all(taxes.mapped("price_include")):
                    # suma e brută: baza se extrage ca pentru o taxă inclusă, apoi TVA-ul se
                    # recalculează pe baza rotunjită, exact ca pe chitanța generată (care primește
                    # netul), ca totalul decontului să fie identic cu cel al chitanței — altfel 542
                    # nu s-ar închide la zero. Față de bon poate rămâne o rotunjire de 1 ban.
                    price_unit = expenses.currency_id.round(
                        taxes.with_context(force_price_include=True).compute_all(
                            expenses.amount, expenses.currency_id, quantity=1, partner=expenses.partner_id
                        )["total_excluded"]
                    )
                tax_info = taxes.compute_all(price_unit, expenses.currency_id, quantity=1, partner=expenses.partner_id)
                tax_amount += sum(t.get("amount", 0.0) for t in tax_info.get("taxes", False))
                price_subtotal = tax_info["total_excluded"]
            expenses.tax_amount = tax_amount
            expenses.price_subtotal = price_subtotal
