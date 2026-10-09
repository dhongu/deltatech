from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.service.model import get_public_method
from odoo.tests import Form, new_test_user, tagged
from odoo.tools import SQL

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleConfirmPayment(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")
        cls.payment_method = cls.env.ref("payment.payment_method_unknown")
        cls.bank_journal = cls.company_data["default_journal_bank"]
        # "none" has no account.payment.method in Odoo, like the wire transfer of payment_custom
        cls.provider = cls._create_provider("none")
        cls.salesman = new_test_user(
            cls.env,
            login="salepay_salesman",
            groups="base.group_user,sales_team.group_sale_salesman",
            company_id=cls.company_data["company"].id,
            company_ids=[Command.set(cls.company_data["company"].ids)],
        )

    @classmethod
    def _create_provider(cls, code, **values):
        return cls.env["payment.provider"].create(
            {
                **values,
                "name": f"Provider {code}",
                "code": code,
                "state": "enabled",
                "journal_id": cls.bank_journal.id,
                "payment_method_ids": [Command.set(cls.payment_method.ids)],
            }
        )

    def _create_order(self, user=None):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "user_id": (user or self.env.user).id,
                "require_signature": False,
                "order_line": [Command.create({"product_id": self.product_a.id, "price_unit": 100.0})],
            }
        )

    def _create_transaction(self, order, amount, state, provider=None):
        return (
            self.env["payment.transaction"]
            .sudo()
            .create(
                {
                    "provider_id": (provider or self.provider).id,
                    "payment_method_id": self.payment_method.id,
                    "amount": amount,
                    "currency_id": order.currency_id.id,
                    "partner_id": order.partner_id.id,
                    "state": state,
                    "is_post_processed": True,
                    "sale_order_ids": [Command.link(order.id)],
                }
            )
        )

    def _wizard(self, order, user=None, **values):
        wizard_model = self.env["sale.confirm.payment"].with_context(active_id=order.id)
        if user:
            wizard_model = wizard_model.with_user(user)
        with Form(wizard_model) as form:
            for field, value in values.items():
                setattr(form, field, value)
        return form.record

    def test_confirm_records_payment_date(self):
        order = self._create_order()
        wizard = self._wizard(order, provider_id=self.provider, payment_date=date(2026, 9, 15))
        self.assertEqual(wizard.amount, order.amount_total, "Without a transaction the rest to pay is proposed")
        wizard.do_confirm()

        tx = order.transaction_ids
        self.assertRecordValues(tx, [{"state": "done", "amount": order.amount_total, "is_post_processed": True}])
        self.assertIn("09/15/2026", tx.state_message)
        self.assertIn("09/15/2026", order.message_ids[0].body)
        self.assertFalse(tx.payment_id, "The provider has no payment method line: no accounting payment")
        self.assertEqual(order.payment_status, "done")
        self.assertEqual(order.state, "sale", "The post-processing confirms the paid quotation")

    def test_confirm_dates_the_accounting_payment(self):
        method = (
            self.env["account.payment.method"]
            .sudo()
            .create({"name": "Manual provider", "code": "salepay_test", "payment_type": "inbound"})
        )
        self.env["account.payment.method.line"].create(
            {
                "payment_method_id": method.id,
                "journal_id": self.bank_journal.id,
                "payment_provider_id": self.provider.id,
            }
        )
        order = self._create_order()
        self._wizard(order, provider_id=self.provider, payment_date=date(2026, 9, 15)).do_confirm()

        payment = order.transaction_ids.payment_id
        self.assertTrue(payment)
        self.assertEqual(payment.date, date(2026, 9, 15))
        self.assertEqual(payment.amount, order.amount_total)

    def test_pending_transaction_is_taken_over(self):
        order = self._create_order()
        tx = self._create_transaction(order, order.amount_total, "pending")
        wizard = self._wizard(order)
        self.assertEqual(wizard.transaction_id, tx)
        self.assertEqual(wizard.amount, order.amount_total)
        wizard.do_confirm()
        self.assertEqual(order.transaction_ids, tx)
        self.assertEqual(tx.state, "done")

    def test_done_transaction_is_not_replaced(self):
        order = self._create_order()
        half = order.amount_total / 2
        tx_done = self._create_transaction(order, half, "done")

        wizard = self._wizard(order, provider_id=self.provider)
        self.assertFalse(wizard.transaction_id, "A confirmed transaction must not be taken over")
        self.assertEqual(wizard.amount, half, "The rest to pay is proposed")
        wizard.do_confirm()

        self.assertTrue(tx_done.exists())
        self.assertEqual(tx_done.state, "done")
        self.assertEqual(len(order.transaction_ids), 2)
        self.assertEqual(order.payment_amount, order.amount_total)
        self.assertEqual(order.payment_status, "done")

    def test_paid_order_proposes_nothing(self):
        order = self._create_order()
        tx_done = self._create_transaction(order, order.amount_total, "done")
        wizard = self._wizard(order, provider_id=self.provider)
        self.assertEqual(wizard.amount, 0.0)
        wizard.do_confirm()
        self.assertEqual(order.transaction_ids, tx_done)

    def test_update_refuses_a_confirmed_transaction(self):
        order = self._create_order()
        tx_done = self._create_transaction(order, order.amount_total, "done")
        wizard = (
            self.env["sale.confirm.payment"]
            .with_context(active_id=order.id)
            .create({"transaction_id": tx_done.id, "provider_id": self.provider.id, "amount": 10.0})
        )
        with self.assertRaises(UserError):
            wizard.do_confirm()
        self.assertTrue(tx_done.exists())
        self.assertEqual(tx_done.amount, order.amount_total)

    def test_authorized_transaction_is_refused(self):
        order = self._create_order()
        tx = self._create_transaction(order, order.amount_total, "pending")
        # A card provider would be needed for a real authorization; the state is what matters here
        self.env.cr.execute(SQL("UPDATE payment_transaction SET state = 'authorized' WHERE id = %s", tx.id))
        tx.invalidate_recordset(["state"])
        wizard = self._wizard(order, provider_id=self.provider)
        self.assertFalse(wizard.transaction_id)
        with self.assertRaises(UserError):
            wizard.do_confirm()
        with self.assertRaises(UserError):
            wizard.do_add_payment()
        self.assertEqual(order.transaction_ids, tx)
        self.assertEqual(tx.state, "authorized")

    def test_salesman_without_invoicing_can_confirm(self):
        self.assertFalse(self.salesman.has_group("account.group_account_invoice"))
        order = self._create_order(user=self.salesman)
        tx = self._create_transaction(order, order.amount_total, "pending")

        wizard = self._wizard(order, user=self.salesman)
        self.assertEqual(wizard.transaction_id, tx)
        wizard.do_confirm()
        self.assertEqual(tx.state, "done")
        self.assertEqual(order.payment_status, "done")

        order_2 = self._create_order(user=self.salesman)
        self._wizard(order_2, user=self.salesman, provider_id=self.provider, amount=50.0).do_add_payment()
        self.assertRecordValues(order_2.transaction_ids, [{"state": "pending", "amount": 50.0}])
        self.assertEqual(order_2.transaction_ids.create_uid, self.salesman)

    def test_salesman_cannot_confirm_others_orders(self):
        order = self._create_order(user=self.env.user)
        with self.assertRaises(AccessError):
            self._wizard(order, user=self.salesman, provider_id=self.provider).do_confirm()
        self.assertFalse(order.transaction_ids)

    def test_post_processing_without_payment_method_line(self):
        order = self._create_order()
        tx = self._create_transaction(order, order.amount_total, "done")
        tx.is_post_processed = False
        # What the cron payment.cron_post_process_payment_tx runs; it raised "Please define a
        # payment method line on your payment." and retried every 10 minutes for 4 days.
        tx._post_process()
        self.assertTrue(tx.is_post_processed)
        self.assertFalse(tx.payment_id)

    def test_wire_transfer_provider(self):
        if "custom" not in dict(self.env["payment.provider"]._fields["code"].selection):
            self.skipTest("payment_custom is not installed")
        provider = self._create_provider("custom", custom_mode="wire_transfer")
        self.assertFalse(
            provider.journal_id.inbound_payment_method_line_ids.filtered(
                lambda line: line.payment_provider_id == provider
            )
        )
        order = self._create_order(user=self.salesman)
        tx = self._create_transaction(order, order.amount_total, "pending", provider=provider)

        self._wizard(order, user=self.salesman).do_confirm()

        self.assertRecordValues(tx, [{"state": "done", "is_post_processed": True, "payment_id": False}])
        self.assertEqual(order.state, "sale")
        self.assertEqual(order.payment_status, "done")

    # SALEPAY-006: the wizard is created and written by any internal user through RPC, the
    # transaction it changes as superuser must belong to the order whose access was checked.

    def test_update_transaction_is_not_callable_remotely(self):
        wizard = self.env["sale.confirm.payment"]
        with self.assertRaisesRegex(AttributeError, "does not exist"):
            get_public_method(wizard, "update_transaction")
        with self.assertRaises(AccessError):
            get_public_method(wizard, "_update_transaction")

    def test_transaction_of_another_order_is_refused(self):
        other_order = self._create_order()
        other_tx = self._create_transaction(other_order, other_order.amount_total, "pending")
        own_order = self._create_order(user=self.salesman)
        wizard = (
            self.env["sale.confirm.payment"]
            .with_user(self.salesman)
            .with_context(active_id=own_order.id)
            .create({"transaction_id": other_tx.id, "provider_id": self.provider.id, "amount": 1.0})
        )
        with self.assertRaises(UserError):
            wizard.do_add_payment()
        with self.assertRaises(UserError):
            wizard.do_confirm()
        self.assertRecordValues(other_tx, [{"state": "pending", "amount": other_order.amount_total}])
        self.assertFalse(own_order.transaction_ids)

    def test_private_update_checks_the_order(self):
        other_order = self._create_order()
        other_tx = self._create_transaction(other_order, other_order.amount_total, "pending")
        own_order = self._create_order(user=self.salesman)
        wizard = (
            self.env["sale.confirm.payment"]
            .with_user(self.salesman)
            .with_context(active_id=own_order.id)
            .create({"transaction_id": other_tx.id, "provider_id": self.provider.id, "amount": 1.0})
        )
        # Even called from Python code, the private method does not trust its caller
        with self.assertRaises(AccessError):
            wizard._update_transaction(other_order.with_user(self.salesman))
        with self.assertRaises(UserError):
            wizard._update_transaction(own_order.with_user(self.salesman))
        self.assertEqual(other_tx.amount, other_order.amount_total)

    def test_provider_of_another_company_is_refused(self):
        other_company = self.env["res.company"].create({"name": "SALEPAY-006 other company"})
        provider = self.env["payment.provider"].create(
            {
                "name": "Other company provider",
                "code": "none",
                "state": "enabled",
                "company_id": other_company.id,
                "payment_method_ids": [Command.set(self.payment_method.ids)],
            }
        )
        order = self._create_order()
        tx = self._create_transaction(order, order.amount_total, "pending")
        wizard = self._wizard(order)
        wizard.provider_id = provider
        with self.assertRaises(UserError):
            wizard.do_confirm()
        self.assertRecordValues(tx, [{"state": "pending", "provider_id": self.provider.id}])

    def test_provider_of_the_parent_company_is_accepted_on_a_branch(self):
        company = self.company_data["company"]
        branch = self.env["res.company"].create({"name": "SALEPAY-008 branch", "parent_id": company.id})
        self.env.user.company_ids |= branch
        order = (
            self.env["sale.order"]
            .with_company(branch)
            .create(
                {
                    "partner_id": self.partner_a.id,
                    "company_id": branch.id,
                    "require_signature": False,
                    "order_line": [Command.create({"product_id": self.product_a.id, "price_unit": 100.0})],
                }
            )
        )
        self.assertEqual(self.provider.company_id, company)
        tx = self._create_transaction(order, order.amount_total, "pending")
        wizard = self._wizard(order.with_company(branch))
        self.assertEqual(wizard.provider_id, self.provider)
        wizard.do_confirm()
        self.assertRecordValues(tx, [{"state": "done", "provider_id": self.provider.id}])

    def test_payment_method_of_another_provider_is_refused(self):
        method = (
            self.env["payment.method"]
            .with_context(active_test=False)
            .search([("id", "!=", self.payment_method.id), ("primary_payment_method_id", "=", False)], limit=1)
        )
        if not method:
            self.skipTest("No other payment method")
        order = self._create_order()
        wizard = self._wizard(order, provider_id=self.provider)
        wizard.payment_method_id = method
        with self.assertRaises(UserError):
            wizard.do_add_payment()
        self.assertFalse(order.transaction_ids)
