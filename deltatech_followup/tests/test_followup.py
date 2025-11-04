from types import SimpleNamespace
from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestDeltatechFollowup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Minimal followup records to exercise logic
        cls.followup_equal = cls.env["account.invoice.followup"].create(
            {
                "name": "Equal match",
                "date_field": "Due date",
                "relative_days": 5,
                "match": "=",
                "only_open": True,
            }
        )
        cls.followup_ge = cls.env["account.invoice.followup"].create(
            {
                "name": "GreaterEqual match",
                "date_field": "Invoice date",
                "relative_days": 0,
                "match": ">=",
                "only_open": True,
            }
        )

    def test_is_match_equal_operator(self):
        today = fields.Date.today(self.env)
        # target_date = base_date + relative_days => base_date = today - relative_days
        base_date = today - relativedelta(days=self.followup_equal.relative_days)
        self.assertTrue(self.followup_equal.is_match(base_date))
        # A day off should not match for '='
        self.assertFalse(self.followup_equal.is_match(base_date - relativedelta(days=1)))

    def test_is_match_greater_equal_operator(self):
        today = fields.Date.today(self.env)
        # With relative_days = 0, target_date is the same as base_date
        # Case 1: base_date = today -> should be True
        self.assertTrue(self.followup_ge.is_match(today))
        # Case 2: base_date in the past -> today >= target_date -> True
        self.assertTrue(self.followup_ge.is_match(today - relativedelta(days=3)))
        # Case 3: base_date in the future -> today >= target_date -> False
        self.assertFalse(self.followup_ge.is_match(today + relativedelta(days=1)))

    def test_send_now_calls_wizard(self):
        # Ensure that calling send_now triggers the wizard's run_followup
        followup = self.env["account.invoice.followup"].create(
            {
                "name": "Call wizard",
                "relative_days": 0,
                "match": "=",
            }
        )
        module_path = "odoo.addons.deltatech_followup.wizard.followup_send.FollowupSendWizard.run_followup"
        with patch(module_path) as mocked_run:
            mocked_run.return_value = None
            # Method is model-level; call on record
            followup.send_now()
            self.assertTrue(mocked_run.called, "run_followup should be called by send_now()")

    def test_is_match_with_negative_relative_days(self):
        today = fields.Date.today(self.env)
        # '=' comparator with negative relative_days: target = base + (-3) => base = today + 3
        followup_eq_neg = self.env["account.invoice.followup"].create(
            {
                "name": "Eq negative",
                "relative_days": -3,
                "match": "=",
            }
        )
        base_date = today + relativedelta(days=3)
        self.assertTrue(followup_eq_neg.is_match(base_date))
        self.assertFalse(followup_eq_neg.is_match(base_date + relativedelta(days=1)))

        # '>=' comparator with negative relative_days: condition is today >= base - 2
        followup_ge_neg = self.env["account.invoice.followup"].create(
            {
                "name": "GE negative",
                "relative_days": -2,
                "match": ">=",
            }
        )
        # Past/near case -> True
        self.assertTrue(followup_ge_neg.is_match(today))  # target = today - 2
        # Far future base -> False (base = today + 3 -> target = today + 1)
        self.assertFalse(followup_ge_neg.is_match(today + relativedelta(days=3)))

    def test_get_amount_residual_behavior(self):
        wizard = self.env["followup.send.wizard"].create({})
        # When using customer currency and refund -> negative residual
        followup_ccy = self.env["account.invoice.followup"].create(
            {
                "name": "Use ccy",
                "use_customer_currency": True,
            }
        )
        invoice_refund = SimpleNamespace(
            move_type="out_refund",
            amount_residual=100.0,
            amount_residual_signed=999.0,
        )
        self.assertEqual(wizard.get_amount_residual(followup_ccy, invoice_refund), -100.0)

        # When not using customer currency -> use amount_residual_signed regardless of type
        followup_no_ccy = self.env["account.invoice.followup"].create(
            {
                "name": "No ccy",
                "use_customer_currency": False,
            }
        )
        invoice_any = SimpleNamespace(
            move_type="out_invoice",
            amount_residual=200.0,
            amount_residual_signed=150.0,
        )
        self.assertEqual(wizard.get_amount_residual(followup_no_ccy, invoice_any), 150.0)

    def test_send_now_creates_wizard_record(self):
        # Patch the wizard's create to ensure it is called with an empty list and run_followup is invoked
        followup = self.env["account.invoice.followup"].create(
            {
                "name": "Create wizard call",
                "relative_days": 0,
                "match": "=",
            }
        )

        create_path = "odoo.addons.deltatech_followup.wizard.followup_send.FollowupSendWizard.create"

        class DummyWizard:
            def run_followup(self, codes=False):
                return None

        with patch(create_path) as mocked_create:
            mocked_create.return_value = DummyWizard()
            followup.send_now()
            self.assertTrue(mocked_create.called, "Wizard create should be called by send_now()")
            # Depending on how the method is patched, the MagicMock may not be bound,
            # so the positional arguments could be either (values,) or (self, values).
            args, kwargs = mocked_create.call_args
            values = None
            if args:
                if len(args) >= 2:
                    # (self, values)
                    values = args[1]
                else:
                    # (values,)
                    values = args[0]
            else:
                # Fallback to common keyword names if used
                values = kwargs.get("vals") or kwargs.get("values")
            self.assertEqual(values, [], "Wizard.create should receive an empty list")
