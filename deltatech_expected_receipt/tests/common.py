# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Baza comună a testelor: terminal, casier, manager, clienți și ajutoarele de încasare.

Rulează pe planul generic, ca testele să meargă și în CI, unde `l10n_ro` nu e instalat:
contul de avans și taxa de 21% se creează aici. Monografia cu conturile românești (419,
4427) e verificată separat, într-o clasă cu `setup_country("ro")`.
"""

from datetime import date, timedelta

from odoo import Command
from odoo.tests import Form

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

GOLDEN = (301.59, 33.17, 3184.27)
GOLDEN_TOTAL = 3519.03


class ExpectedReceiptCommon(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.journal = cls.env["account.journal"].create(
            {"name": "ING POS", "code": "INGP", "type": "bank", "company_id": cls.company.id}
        )
        cls.suspense = cls.journal.suspense_account_id
        cls.suspense.reconcile = True
        cls.cashier = cls._user(
            "cashier",
            [
                "deltatech_expected_receipt.group_cashier",
                "sales_team.group_sale_manager",
                "account.group_account_readonly",
            ],
        )
        cls.manager = cls._user(
            "manager", ["deltatech_expected_receipt.group_manager", "account.group_account_manager"]
        )
        cls.terminal = cls.env["deltatech.card.terminal"].create(
            {"name": "ING Shop", "user_id": cls.cashier.id, "journal_id": cls.journal.id}
        )
        cls.partners = cls.env["res.partner"].create([{"name": "Glassmart"}, {"name": "Mansoor"}, {"name": "Davinox"}])
        cls.day = date(2026, 8, 21)
        cls.downpayment_account = cls._downpayment_account()
        cls.company.downpayment_account_id = cls.downpayment_account
        cls.tax_21 = cls.tax_sale_a.copy({"name": "VAT 21%", "amount": 21.0})
        cls.product_a.taxes_id = cls.tax_21

    @classmethod
    def _downpayment_account(cls):
        return cls.env["account.account"].create(
            {
                "name": "Customer advances",
                "code": "419000",
                "account_type": "liability_current",
                "company_ids": [Command.set(cls.company.ids)],
            }
        )

    @classmethod
    def _account(cls, code):
        return cls.env["account.account"].search(
            [("code", "=like", code + "%"), ("company_ids", "in", cls.company.ids)], order="code", limit=1
        )

    @classmethod
    def _user(cls, login, groups):
        return cls.env["res.users"].create(
            {
                "name": login.title(),
                "login": f"er_{login}",
                "email": f"{login}@example.com",
                "company_id": cls.company.id,
                "company_ids": [Command.set(cls.company.ids)],
                "group_ids": [Command.set([cls.env.ref(xmlid).id for xmlid in ["base.group_user", *groups]])],
            }
        )

    # ------------------------------------------------------------------
    def _pay(self, partner=None, amount=100.0, day=None, user=None, record=None, **values):
        """Încasare prin dialog, ca în realitate (plată + rând în registru)."""
        user = user or self.manager
        context = {"active_model": record._name, "active_id": record.id} if record else {}
        with Form(self.env["deltatech.card.payment"].with_user(user).with_context(**context)) as form:
            if not record:
                form.partner_id = partner
            form.terminal_id = values.pop("terminal_id", self.terminal)
            # Modul de facturare întâi: onchange-ul lui repropune suma.
            for name, value in values.items():
                setattr(form, name, value)
            form.amount = amount
            form.date = day or self.day
        form.record.action_confirm()
        return self.env["deltatech.expected.receipt"].search([], order="id desc", limit=1)

    def _order(self, partner=None, qty=1, confirm=True, user=None):
        order = (
            self.env["sale.order"]
            .with_user(user or self.cashier)
            .create(
                {
                    "partner_id": (partner or self.partners[0]).id,
                    "order_line": [Command.create({"product_id": self.product_a.id, "product_uom_qty": qty})],
                }
            )
        )
        if confirm:
            order.action_confirm()
        return order

    def _statement_line(self, amount, day=None, journal=None):
        return self.env["account.bank.statement.line"].create(
            {
                "journal_id": (journal or self.journal).id,
                "date": day or self.day,
                "payment_ref": "ING POS",
                "amount": amount,
            }
        )

    def _settlement(self, statement_line, **values):
        wizard = (
            self.env["deltatech.card.settlement"]
            .with_user(self.manager)
            .create({"statement_line_id": statement_line.id, "company_id": self.company.id, **values})
        )
        wizard.action_search()
        return wizard

    def _golden_receipts(self):
        return self.env["deltatech.expected.receipt"].concat(
            *[
                self._pay(partner, amount, self.day - timedelta(days=offset))
                for partner, amount, offset in zip(self.partners, GOLDEN, (1, 2, 3), strict=True)
            ]
        )

    def _reconcile_elsewhere(self, receipt, statement_line):
        """Reconcilierea făcută de contabil din ecranul standard, nu din decontare."""
        _liquidity, suspense, _other = statement_line._seek_for_lines()
        (suspense | receipt._settlement_lines()).reconcile()
