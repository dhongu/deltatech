# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""„Încasare cu cardul”: scrie plata în clipa în care clientul plătește.

Se deschide de pe comandă, de pe factură sau din registru, pe client. Nota contabilă e
5125 = 4111: banii sunt ai firmei, dar încă nu sunt în cont. Decontarea stinge 5125 când
vine extrasul băncii.

Pe o comandă nefacturată, plata e un avans. TVA-ul devine exigibil la încasarea avansului
(Codul fiscal, art. 282 alin. (2) lit. b), iar factura de avans e obligatorie (art. 319
alin. (6) lit. d). De aceea varianta implicită emite factura de avans și încasează pe ea.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
from odoo.tools.misc import formatLang

from ..models.expected_receipt import LIVE_STATES


class CardPayment(models.TransientModel):
    _name = "deltatech.card.payment"
    _description = "Card Payment"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one(
        "res.partner",
        "Customer",
        required=True,
        domain="['|', ('parent_id', '=', False), ('is_company', '=', True)]",
    )
    sale_order_id = fields.Many2one("sale.order", "Sales Order", readonly=True)
    invoice_id = fields.Many2one(
        "account.move",
        "Invoice",
        domain="[('partner_id', 'child_of', partner_id), ('move_type', '=', 'out_invoice'), "
        "('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial')), "
        "('company_id', '=', company_id)]",
    )
    invoice_mode = fields.Selection(
        [
            ("invoice", "Pay an issued invoice"),
            ("downpayment", "Issue a down payment invoice"),
            ("none", "No invoice (credit on the customer)"),
        ],
        default="none",
        required=True,
        help="On an order that is not invoiced, the payment is a down payment: the VAT becomes due "
        "when it is received and a down payment invoice must be issued.",
    )
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary("Amount Received", required=True)
    amount_due = fields.Monetary(readonly=True)
    amount_left = fields.Monetary("Remaining Due", compute="_compute_amount_left")
    date = fields.Date("Receipt Date", required=True, default=fields.Date.context_today)
    terminal_id = fields.Many2one(
        "deltatech.card.terminal",
        "Terminal",
        required=True,
        check_company=True,
        default=lambda self: self.env["deltatech.card.terminal"]._default_for_user(),
    )
    note = fields.Char()
    warning = fields.Char(compute="_compute_warning")
    done = fields.Boolean(readonly=True, copy=False)

    # ------------------------------------------------------------------
    @api.model
    def _open_for(self, record):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Card Payment"),
            "res_model": self._name,
            "views": [[False, "form"]],
            "target": "new",
            "context": {"active_model": record._name, "active_id": record.id},
        }

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        if model == "sale.order" and active_id:
            order = self.env["sale.order"].browse(active_id)
            values.update(
                sale_order_id=order.id,
                partner_id=order.partner_id.id,
                company_id=order.company_id.id,
                currency_id=order.currency_id.id,
            )
            open_invoices = self._open_invoices(order)
            if open_invoices:
                values.update(invoice_mode="invoice", invoice_id=open_invoices[0].id)
                values["amount_due"] = open_invoices[0].amount_residual
            else:
                values.update(invoice_mode="downpayment", amount_due=self._order_amount_due(order))
        elif model == "account.move" and active_id:
            move = self.env["account.move"].browse(active_id)
            values.update(
                invoice_id=move.id,
                invoice_mode="invoice",
                partner_id=move.partner_id.id,
                company_id=move.company_id.id,
                currency_id=move.currency_id.id,
                amount_due=move.amount_residual,
            )
        if values.get("amount_due") and "amount" in fields_list:
            values["amount"] = values["amount_due"]
        return values

    @api.model
    def _open_invoices(self, order):
        return order.invoice_ids.filtered(
            lambda move: move.move_type == "out_invoice"
            and move.state == "posted"
            and move.payment_state in ("not_paid", "partial")
        ).sorted("invoice_date")

    @api.model
    def _order_amount_due(self, order):
        """Cât mai e de încasat pe o comandă: totalul minus ce s-a facturat deja și minus
        încasările cu cardul încă nefacturate."""
        invoiced = sum(
            order.invoice_ids.filtered(lambda m: m.state == "posted" and m.move_type == "out_invoice").mapped(
                "amount_total"
            )
        )
        receipts = (
            self.env["deltatech.expected.receipt"]
            .sudo()
            .search([("sale_order_id", "=", order.id), ("invoice_id", "=", False), ("state", "in", LIVE_STATES)])
        )
        return max(order.amount_total - invoiced - sum(receipts.mapped("amount")), 0.0)

    @api.onchange("invoice_mode", "invoice_id")
    def _onchange_invoice_mode(self):
        if self.invoice_mode == "invoice" and self.invoice_id:
            self.amount_due = self.invoice_id.amount_residual
            self.amount = self.amount_due
        elif self.invoice_mode != "invoice":
            self.invoice_id = False
            if self.sale_order_id:
                self.amount_due = self._order_amount_due(self.sale_order_id)
                self.amount = self.amount_due

    @api.depends("amount", "amount_due")
    def _compute_amount_left(self):
        for wizard in self:
            wizard.amount_left = max(wizard.amount_due - wizard.amount, 0.0)

    @api.depends("amount", "amount_due", "terminal_id", "invoice_mode", "sale_order_id", "currency_id")
    def _compute_warning(self):
        for wizard in self:
            message = ""
            account = wizard.terminal_id.journal_id.suspense_account_id
            if wizard.terminal_id and not account:
                message = self.env._(
                    "Journal %s has no suspense account (5125): the payment would have nowhere to wait.",
                    wizard.terminal_id.journal_id.display_name,
                )
            elif wizard.sale_order_id and wizard.invoice_mode == "none":
                message = self.env._(
                    "A payment received before invoicing is a down payment: the VAT is due on receipt and "
                    "a down payment invoice is required."
                )
            elif wizard.amount_due and (
                float_compare(wizard.amount, wizard.amount_due, precision_rounding=wizard.currency_id.rounding) > 0
            ):
                message = self.env._("The amount exceeds the amount due; the difference stays as customer credit.")
            wizard.warning = message

    # ------------------------------------------------------------------
    def action_confirm(self):
        self.ensure_one()
        if self.done:
            raise UserError(self.env._("The card payment has already been registered."))
        self._check_ready()
        self.done = True
        invoice = self.invoice_id
        if self.invoice_mode == "downpayment":
            invoice = self._create_downpayment_invoice()
        payment = self._create_payment()
        # Casierul nu are drept de creare pe registru: singurul drum e acest dialog.
        receipt = (
            self.env["deltatech.expected.receipt"]
            .sudo()
            .create(
                {
                    "kind": "card",
                    "state": "pending",
                    "partner_id": self.partner_id.id,
                    "sale_order_id": self.sale_order_id.id,
                    "invoice_id": invoice.id,
                    "amount": self.amount,
                    "currency_id": self.currency_id.id,
                    "date": self.date,
                    "terminal_id": self.terminal_id.id,
                    "user_id": self.env.user.id,
                    "payment_id": payment.id,
                    "company_id": self.company_id.id,
                    "note": self.note,
                }
            )
        )
        if invoice:
            self._reconcile_with_invoice(payment, invoice)
        self._log_on_documents(receipt, invoice)
        return {"type": "ir.actions.act_window_close"}

    def _check_ready(self):
        """Tot ce se verifică înainte de `sudo`.

        Plata se scrie cu `sudo`, ca agenții care încasează să nu primească drepturi
        contabile; metoda asta e singura poartă și nu se bazează pe nimic din formular
        fără verificare.
        """
        self.ensure_one()
        user = self.env.user
        if not (
            user.has_group("deltatech_expected_receipt.group_cashier")
            or user.has_group("deltatech_expected_receipt.group_manager")
        ):
            raise UserError(self.env._("You are not allowed to register card payments."))
        if self.company_id not in self.env.companies:
            raise UserError(self.env._("The selected company is not one of your companies."))
        if self.terminal_id.company_id != self.company_id:
            raise UserError(self.env._("Terminal %s belongs to another company.", self.terminal_id.name))
        commercial = self.partner_id.commercial_partner_id
        for doc in (self.sale_order_id, self.invoice_id):
            if not doc:
                continue
            doc.check_access("read")
            if doc.company_id != self.company_id:
                raise UserError(self.env._("Document %s belongs to another company.", doc.display_name))
            if doc.partner_id.commercial_partner_id != commercial:
                raise UserError(
                    self.env._(
                        "Document %(doc)s does not belong to %(partner)s.",
                        doc=doc.display_name,
                        partner=commercial.display_name,
                    )
                )
        if self.sale_order_id and self.sale_order_id.state == "cancel":
            raise UserError(self.env._("The order is cancelled."))
        if self.invoice_mode == "invoice":
            invoice = self.invoice_id
            if not invoice:
                raise UserError(self.env._("Select the invoice that is paid."))
            if invoice.state != "posted" or invoice.move_type != "out_invoice":
                raise UserError(self.env._("Only a posted customer invoice can be paid."))
        if (
            self.sale_order_id
            and self.invoice_mode == "none"
            and not user.has_group("deltatech_expected_receipt.group_manager")
        ):
            raise UserError(
                self.env._(
                    "A payment on a sales order is a down payment and needs a down payment invoice. "
                    "Only a manager can register it without one."
                )
            )
        if self.invoice_mode == "downpayment" and not self.sale_order_id:
            raise UserError(self.env._("A down payment invoice is issued from a sales order."))
        if float_is_zero(self.amount, precision_rounding=self.currency_id.rounding) or self.amount < 0:
            raise UserError(self.env._("The received amount must be greater than zero."))
        journal = self.terminal_id.journal_id
        account = journal.suspense_account_id
        if not account:
            raise UserError(self.env._("Journal %s has no suspense account (5125).", journal.display_name))
        if not account.reconcile:
            raise UserError(
                self.env._(
                    "Account %s does not allow reconciliation, so the payment could never be matched "
                    "with the bank statement. Enable 'Allow Reconciliation' on it.",
                    account.display_name,
                )
            )

    def _create_downpayment_invoice(self):
        """Factura de avans din comandă, pe suma încasată, postată imediat.

        Se folosește asistentul standard de avans din `sale`, ca factura să fie legată de
        comandă și să fie dedusă la facturarea finală.
        """
        order = self.sale_order_id.sudo()
        if order.state != "sale":
            # Clientul plătește oferta: plata confirmă comanda, iar avansul se facturează
            # doar pe o comandă confirmată.
            order.action_confirm()
        advance = (
            self.env["sale.advance.payment.inv"]
            .sudo()
            .with_context(active_model="sale.order", active_ids=order.ids)
            .create(
                {
                    "advance_payment_method": "fixed",
                    "fixed_amount": self.amount,
                    "sale_order_ids": [(6, 0, order.ids)],
                }
            )
        )
        invoice = advance._create_invoices(order)
        invoice.invoice_date = self.date
        invoice.action_post()
        return invoice

    def _create_payment(self):
        journal = self.terminal_id.journal_id
        account = journal.suspense_account_id
        payment = (
            self.env["account.payment"]
            .sudo()
            .create(
                {
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": self.partner_id.id,
                    "amount": self.amount,
                    "currency_id": self.currency_id.id,
                    "date": self.date,
                    "journal_id": journal.id,
                    "memo": self._payment_memo(),
                    "company_id": self.company_id.id,
                }
            )
        )
        # `outstanding_account_id` e calculat din metoda de plată: se scrie după creare,
        # altfel ar fi recalculat în aceeași scriere.
        payment.outstanding_account_id = account
        payment.action_post()
        if not payment.move_id.line_ids.filtered(lambda line: line.account_id == account):
            raise UserError(
                self.env._(
                    "The payment did not reach the suspense account %s. Check the payment methods of journal %s.",
                    account.display_name,
                    journal.display_name,
                )
            )
        return payment

    def _payment_memo(self):
        document = self.invoice_id.name or self.sale_order_id.name or ""
        return " · ".join(part for part in (self.env._("Card %s", self.terminal_id.name), document) if part)

    def _reconcile_with_invoice(self, payment, invoice):
        payment = payment.sudo()
        account = payment.destination_account_id
        if not account.reconcile:
            return
        lines = (payment.move_id.line_ids | invoice.sudo().line_ids).filtered(
            lambda line: line.account_id == account and not line.reconciled
        )
        if len(lines) > 1:
            lines.reconcile()

    def _log_on_documents(self, receipt, invoice):
        body = self.env._(
            "Card payment: %(amount)s on terminal %(terminal)s, %(date)s, by %(user)s. Waiting for settlement.",
            amount=formatLang(self.env, self.amount, currency_obj=self.currency_id),
            terminal=self.terminal_id.name,
            date=fields.Date.to_string(self.date),
            user=self.env.user.name,
        )
        for record in (self.sale_order_id, invoice):
            if record:
                record.sudo().message_post(body=body, subtype_xmlid="mail.mt_note")
        if self.sale_order_id and self.invoice_mode == "none":
            receipt.message_post(
                body=self.env._("Down payment received without a down payment invoice."),
                subtype_xmlid="mail.mt_note",
            )
