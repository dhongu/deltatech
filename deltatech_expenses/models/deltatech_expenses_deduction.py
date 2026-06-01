# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError


class DeltatechExpensesDeduction(models.Model):
    _name = "deltatech.expenses.deduction"
    _inherit = ["mail.thread"]
    _description = "Expenses Deduction"
    _order = "date_expense desc, id desc"
    _rec_name = "number"

    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency_id or journal.company_id.currency_id or self.env.user.company_id.currency_id

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
        account_pool = self.env["account.account"]
        try:
            account_id = account_pool.search(
                [("code", "=ilike", "625%"), ("company_id", "=", self.env.company.id)], limit=1
            )  # Cheltuieli cu deplasari
        except Exception:
            try:
                account_id = account_pool.search(
                    [("account_type", "=", "expense"), ("company_id", "=", self.env.company.id)], limit=1
                )
            except Exception:
                account_id = False
        return account_id

    number = fields.Char(string="Number", size=32, readonly=True, default="/")
    state = fields.Selection(
        [("draft", "Draft"), ("advance", "Advance"), ("done", "Done"), ("cancel", "Cancelled")],
        string="Status",
        index=True,
        readonly=True,
        tracking=True,
        default="draft",
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed expenses deduction. \
            \n* The 'Done' status is set automatically when the expenses deduction is confirm.  \
            \n* The 'Cancelled' status is used when user cancel expenses deduction.",
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

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
        required=True,
        default=lambda self: self._default_currency(),
        compute="_compute_currency",
    )

    journal_id = fields.Many2one(
        "account.journal",
        string="Cash Journal",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
        default=lambda self: self._default_journal(),
    )
    expense_journal_id = fields.Many2one("account.journal", string="Expense Journal")

    journal_diem_id = fields.Many2one(
        "account.journal",
        string="Diem Journal",
        default=lambda self: self._default_journal_diem(),
    )

    account_diem_id = fields.Many2one(
        "account.account",
        string="Account",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)], "advance": [("readonly", False)]},
        default=lambda self: self._default_account_diem(),
    )

    move_id = fields.Many2one("account.move", string="Account Entry", readonly=True)
    # move_ids = fields.One2many("account.move.line", related="move_id.line_ids", string="Journal Items", readonly=True)
    move_ids = fields.Many2many("account.move.line", string="Journal Items", readonly=True, compute="_compute_move_ids")

    diem = fields.Monetary(
        string="Diem",
        readonly=True,
        # states={"draft": [("readonly", False)], "advance": [("readonly", False)]},
        default=42.5,
    )
    days = fields.Integer(
        string="Days",
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

    @api.depends("expenses_line_ids", "days", "diem", "advance")
    def _compute_amount(self):
        for expense in self:
            total = 0.0
            for line in expense.expenses_line_ids:
                total += line.tax_amount + line.price_subtotal

            expense.amount_vouchers = total
            expense.total_diem = expense.days * expense.diem
            expense.amount = expense.amount_vouchers + expense.total_diem

            expense.difference = expense.amount - expense.advance

    def _compute_currency(self):
        for expense in self:
            expense.currency_id = expense.company_id.currency_id.id

    def unlink(self):
        for t in self:
            if t.state not in ("draft", "cancel"):
                raise UserError(self.env._("Cannot delete Expenses Deduction(s) which are already done."))
        return super().unlink()

    def invalidate_expenses(self):
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

            # eliberăm cheltuielile hr.expense preluate: ștergem liniile importate, iar override-ul
            # unlink dezleagă cheltuiala (expenses_deduction_id=False), redevenind disponibilă pentru
            # fluxul standard sau o nouă preluare. Liniile introduse manual rămân pentru re-validare.
            expenses.expenses_line_ids.filtered("hr_expense_id").unlink()

        # todo: de facut cancel dupa expenses_line_ids
        # for expenses in self:
        #    expenses.line_ids.cancel_voucher()
        #    expenses.line_ids.action_cancel_draft()

        # statement_lines = self.env["account.bank.statement.line"].search([("expenses_deduction_id", "=", expenses.id)])
        # if statement_lines:
        #     statement_lines.unlink()

        return True

    def _eligible_hr_expenses(self):
        """Cheltuielile hr.expense ale angajatului care pot fi preluate în decont:
        aprobate/depuse, fără notă contabilă proprie și nelegate de alt decont."""
        self.ensure_one()
        if not self.employee_id:
            return self.env["hr.expense"]
        return self.env["hr.expense"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("company_id", "=", self.company_id.id),
                ("expenses_deduction_id", "=", False),
                ("state", "in", ("submitted", "approved")),
                ("account_move_id", "=", False),
            ]
        )

    def _import_hr_expenses(self, expenses):
        """Creează linii de decont din cheltuielile hr.expense date și le leagă de decont
        (setând expenses_deduction_id), astfel încât contabilizarea să se facă doar aici."""
        self.ensure_one()
        line_model = self.env["deltatech.expenses.deduction.line"]
        expenses = expenses.filtered(lambda e: not e.expenses_deduction_id)
        for expense in expenses:
            # Linia de decont interpretează `amount` conform flag-ului price_include al taxelor
            # (compute_all pe aceleași taxe). Pentru taxe „TVA inclus" trimitem brutul, pentru taxe
            # „pe deasupra" (non-price-include) trimitem netul, ca subtotalul + TVA-ul să corespundă
            # exact cu cheltuiala hr.expense.
            taxes = expense.tax_ids
            price_include = bool(taxes) and all(taxes.mapped("price_include"))
            line_amount = expense.total_amount if price_include else expense.untaxed_amount
            line_model.create(
                {
                    "expenses_deduction_id": self.id,
                    "hr_expense_id": expense.id,
                    "name": expense.name,
                    "date": expense.date,
                    "amount": line_amount,
                    "tax_ids": [(6, 0, expense.tax_ids.ids)],
                    "partner_id": expense.vendor_id.id,
                    "expense_account_id": expense.account_id.id,
                    "analytic_distribution": expense.analytic_distribution,
                    "type": "expenses",
                    "currency_id": expense.currency_id.id,
                }
            )
        if expenses:
            expenses.sudo().write({"expenses_deduction_id": self.id})
        return True

    def action_open_import_hr_expenses(self):
        self.ensure_one()
        if self.state not in ("draft", "advance"):
            raise UserError(self.env._("Cheltuielile pot fi preluate doar într-un decont în starea Draft sau Advance."))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Preia cheltuieli HR"),
            "res_model": "deltatech.expenses.import.hr",
            "view_mode": "form",
            "target": "new",
            "context": {"default_expenses_deduction_id": self.id},
        }

    def validate_advance(self):
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
                value_lines = [
                    {
                        "partner_id": expenses.partner_id.id,
                        "account_id": account.id,
                        "name": self.env._("Avans"),
                        "debit": expenses.advance,
                    },
                    {
                        "partner_id": expenses.partner_id.id,
                        "account_id": expenses.journal_id.default_account_id.id,
                        "name": self.env._("Avans"),
                        "credit": expenses.advance,
                    },
                ]
                value["line_ids"] = [(0, 0, x) for x in value_lines]
                move = self.env["account.move"].create(value)
                move._post()

            expenses.write({"state": "advance", "number": name})

    def _create_advance_settlement(self, expenses, partner, amount, date, ref, payable_account=None):
        """Notă de decontare a cheltuielii din avans: Dr cont furnizor (401) = Cr 542.

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
        account_542 = expenses.expense_journal_id.default_account_id
        move = self.env["account.move"].create(
            {
                "journal_id": expenses.expense_journal_id.id,
                "date": date or expenses.date_expense,
                "ref": ref,
                "expenses_deduction_id": expenses.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": partner.id,
                            "account_id": payable_account.id,
                            "name": self.env._("Decontare avans"),
                            "debit": amount,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "partner_id": partner.id,
                            "account_id": account_542.id,
                            "name": self.env._("Decontare avans"),
                            "debit": 0.0,
                            "credit": amount,
                        },
                    ),
                ],
            }
        )
        move._post()
        return move

    def _reconcile_supplier_payment(self, settle_payable):
        """Reconciliază linia de furnizor a unei plăți directe (supplier_payment) cu datoriile
        deschise ale aceluiași furnizor pe același cont (ca o plată: stinge facturile existente).
        Dacă furnizorul nu are datorii deschise, linia rămâne deschisă (avans către furnizor)."""
        settle_payable.ensure_one()
        open_lines = self.env["account.move.line"].search(
            [
                ("partner_id", "=", settle_payable.partner_id.id),
                ("account_id", "=", settle_payable.account_id.id),
                ("parent_state", "=", "posted"),
                ("reconciled", "=", False),
                ("balance", "<", 0.0),  # datorii deschise (credit furnizor)
                ("id", "!=", settle_payable.id),
            ]
        )
        if open_lines:
            (settle_payable | open_lines).reconcile()

    def validate_expenses(self):
        # poate ar fi bine daca  bonurile fiscale de la acelasi furnizor sa fie unuite intr-o singura chitanta.

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
            expenses_vals = {"state": "done", "number": name}
            vouchers = self.env["account.move"]

            # reconcile = self.env['account.full.reconcile'].create({'name':name})

            for line in expenses.expenses_line_ids:
                partner_id = line.partner_id or partner_generic
                if not partner_id:
                    raise UserError(self.env._("You must select a supplier for all lines."))
                if line.type == "expenses":
                    voucher_value = {
                        "partner_id": partner_id.id,
                        "move_type": "in_receipt",
                        # "pay_now": "pay_now",
                        "invoice_date": line.date,
                        "date": line.date,
                        "ref": line.name,
                        "journal_id": purchase_journal.id,
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
                                    "price_unit": line.price_subtotal,
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
                    settle = self._create_advance_settlement(
                        expenses,
                        payable.partner_id,
                        payable.credit,
                        voucher.date,
                        name,
                        payable_account=payable.account_id,
                    )
                    settle_payable = settle.line_ids.filtered(lambda aml: aml.account_id == payable.account_id)
                    (payable | settle_payable).reconcile()

            # marchează chitanțele fără sold drept plătite
            vouchers.set_paid()

            # Create the account move record.
            line_ids = []

            if expenses.difference:
                account = expenses.expense_journal_id.default_account_id
                # amount = -expenses.difference + expenses.amount_vouchers
                amount = abs(expenses.difference)
                if expenses.difference < 0:
                    value_lines = [
                        {
                            "partner_id": expenses.partner_id.id,
                            "account_id": account.id,
                            "name": self.env._("Deferenta Avans"),
                            "credit": amount,
                        },
                        {
                            "partner_id": expenses.partner_id.id,
                            "account_id": expenses.journal_id.default_account_id.id,
                            "name": self.env._("Deferenta Avans"),
                            "debit": amount,
                        },
                    ]
                else:
                    value_lines = [
                        {
                            "partner_id": expenses.partner_id.id,
                            "account_id": account.id,
                            "name": self.env._("Deferenta Avans"),
                            "debit": amount,
                        },
                        {
                            "partner_id": expenses.partner_id.id,
                            "account_id": expenses.journal_id.default_account_id.id,
                            "name": self.env._("Deferenta Avans"),
                            "credit": amount,
                        },
                    ]
                value = {
                    "journal_id": expenses.journal_id.id,
                    "date": expenses.date_advance,
                    "ref": expenses.number,
                    "expenses_deduction_id": expenses.id,
                }

                value["line_ids"] = [(0, 0, x) for x in value_lines]
                move = self.env["account.move"].create(value)
                move._post()

            if expenses.total_diem:
                move_line_dr = {
                    "name": self.env._("Diurna"),
                    "debit": expenses.total_diem,
                    "credit": 0.0,
                    "account_id": expenses.account_diem_id.id,
                    "journal_id": expenses.journal_diem_id.id,
                    "partner_id": expenses.partner_id.id,
                    "date": expenses.date_expense,
                    "date_maturity": expenses.date_expense,
                }
                move_line_cr = {
                    "name": self.env._("Diurna"),
                    "debit": 0.0,
                    "credit": expenses.total_diem,
                    "account_id": expenses.expense_journal_id.default_account_id.id,  # 542
                    "journal_id": expenses.journal_diem_id.id,
                    "partner_id": expenses.partner_id.id,
                    "date": expenses.date_expense,
                    "date_maturity": expenses.date_expense,
                }
                line_ids.append([0, False, move_line_dr])
                line_ids.append([0, False, move_line_cr])
                move = self.env["account.move"].create(
                    {
                        # "name": name or "/",
                        "journal_id": expenses.journal_diem_id.id,
                        "date": expenses.date_expense,
                        "ref": name or "",
                        "line_ids": line_ids,
                    }
                )
                expenses_vals["move_id"] = move.id
                move.action_post()

            expenses.write(expenses_vals)

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
        self.write({"state": "cancel"})
        return True


class DeltatechExpensesDeductionLine(models.Model):
    _name = "deltatech.expenses.deduction.line"
    _inherit = "analytic.mixin"
    _description = "Expenses Deduction Line"

    @api.model
    def _default_expense_account(self):
        account_pool = self.env["account.account"]
        account = account_pool.search([("code", "=ilike", "623%")], limit=1)  # cheltuieli de protocol
        if not account:
            account = account_pool.search([("account_type", "=", "expense")], limit=1)
        return account

    expenses_deduction_id = fields.Many2one("deltatech.expenses.deduction", string="Expenses Deduction", required=False)
    hr_expense_id = fields.Many2one(
        "hr.expense",
        string="HR Expense",
        copy=False,
        readonly=True,
        help="Cheltuiala hr.expense din care a fost preluată această linie.",
    )
    date = fields.Date("Date", index=True, copy=False, default=fields.Date.context_today)
    name = fields.Text(string="Reference", required=True)
    tax_ids = fields.Many2many("account.tax", string="Tax", help="Only for tax excluded from price")

    type = fields.Selection([("expenses", "Expenses"), ("supplier_payment", "Supplier Payment")], default="expenses")

    amount = fields.Monetary(string="Total")  # e cu tot cu tva ?
    tax_amount = fields.Monetary(readonly=True, store=True, compute="_compute_subtotal")
    price_subtotal = fields.Monetary(readonly=True, store=True, compute="_compute_subtotal")  # valoare subtotal

    # todo: de scos required si de acompletat cu partner_generic in situatia in care nu se completeaza nimic
    partner_id = fields.Many2one("res.partner", string="Partner")
    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True, default=lambda self: self._get_currency()
    )

    expense_account_id = fields.Many2one(
        "account.account", default=lambda self: self._default_expense_account(), string="Default Expense Account"
    )

    state = fields.Selection(related="expenses_deduction_id.state")

    @api.model
    def _get_currency(self):
        journal = self.env["account.journal"].browse(self.env.context.get("journal_id", False))
        if journal.currency_id:
            return journal.currency_id.id
        return self.env.user.company_id.currency_id.id

    @api.model
    def _get_company(self):
        return self.env.context.get("company_id", self.env.user.company_id.id)

    @api.depends("amount", "tax_ids")
    def _compute_subtotal(self):
        for expenses in self:
            tax_amount = 0.0
            price_subtotal = expenses.amount
            if expenses.tax_ids:
                tax_info = expenses.tax_ids.compute_all(
                    expenses.amount, expenses.currency_id, quantity=1, partner=expenses.partner_id
                )
                tax_amount += sum(t.get("amount", 0.0) for t in tax_info.get("taxes", False))
                price_subtotal = tax_info["total_excluded"]
            expenses.tax_amount = tax_amount
            expenses.price_subtotal = price_subtotal

    def unlink(self):
        # eliberăm cheltuielile hr.expense preluate, ca să nu rămână blocate de la postarea standard
        linked_expenses = self.mapped("hr_expense_id")
        res = super().unlink()
        if linked_expenses:
            linked_expenses.sudo().write({"expenses_deduction_id": False})
        return res
