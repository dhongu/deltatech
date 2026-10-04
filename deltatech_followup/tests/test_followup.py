# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestFollowup(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids += cls.env.ref("deltatech_followup.group_manage_followups")
        cls.today = fields.Date.context_today(cls.env["account.invoice.followup"])
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Followup Customer",
                "email": "followup.customer@example.com",
                "lang": "en_US",
                "send_followup": True,
            }
        )
        cls.other_customer = cls.env["res.partner"].create(
            {"name": "No Followup Customer", "email": "nofollowup@example.com", "lang": "en_US"}
        )
        cls.override_partner = cls.env["res.partner"].create(
            {"name": "Override Partner", "email": "override@example.com"}
        )
        cls.template = cls.env["mail.template"].create(
            {
                "name": "Followup template",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "subject": "Followup",
                "email_from": "company@example.com",
                "partner_to": "{{ object.id }}",
                "body_html": "<div>Dear ${object.name}, total $total_debit, all $total_all_debit, "
                "due $total_due_debit $currency [invoices]</div>",
            }
        )
        cls.invoice_html = "<p>INV:$number|$date_invoice|$date_due|$amount_total|$amount_due|$currency</p>"
        cls.invoice = cls._create_move(cls.customer, 100.0, cls.today - relativedelta(days=10), 5)
        cls.wizard = cls.env["followup.send.wizard"]

    @classmethod
    def _create_move(cls, partner, price, invoice_date, due_days_ago, move_type="out_invoice", post=True):
        move = cls.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "invoice_date": invoice_date,
                "invoice_date_due": cls.today - relativedelta(days=due_days_ago),
                "invoice_line_ids": [
                    (0, 0, {"name": "Service", "quantity": 1, "price_unit": price, "tax_ids": [(6, 0, [])]})
                ],
            }
        )
        if post:
            move.action_post()
        return move

    def _create_followup(self, **vals):
        values = {
            "name": "Followup",
            "code": "F5",
            "date_field": "Due date",
            "relative_days": 5,
            "match": "=",
            "mail_template": self.template.id,
            "invoice_html": self.invoice_html,
            "amount_margin": 1.0,
        }
        values.update(vals)
        return self.env["account.invoice.followup"].create(values)

    def _mails(self):
        return self.env["mail.mail"].search([("model", "=", "res.partner"), ("res_id", "=", self.customer.id)])

    # ------------------------------------------------------------------
    # account.invoice.followup
    # ------------------------------------------------------------------
    def test_defaults(self):
        followup = self.env["account.invoice.followup"].create({"name": "Defaults"})
        self.assertTrue(followup.active)
        self.assertEqual(followup.date_field, "Due date")
        self.assertEqual(followup.match, "=")
        self.assertTrue(followup.only_open)
        self.assertFalse(followup.with_refunds)
        self.assertFalse(followup.use_customer_currency)
        self.assertEqual(followup.amount_margin, 1.0)
        self.assertFalse(self.other_customer.send_followup)
        self.assertTrue(self.customer.send_followup)

    def test_access_requires_followup_group(self):
        user = self.env["res.users"].create(
            {
                "name": "No Followup Group",
                "login": "no_followup_group",
                "group_ids": [(6, 0, [self.env.ref("account.group_account_invoice").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.env["account.invoice.followup"].with_user(user).create({"name": "Denied"})

    def test_is_match_equal(self):
        followup = self._create_followup(relative_days=5, match="=")
        self.assertTrue(followup.is_match(self.today - relativedelta(days=5)))
        self.assertFalse(followup.is_match(self.today - relativedelta(days=6)))
        self.assertFalse(followup.is_match(self.today))

    def test_is_match_greater_or_equal(self):
        followup = self._create_followup(relative_days=-3, match=">=")
        self.assertTrue(followup.is_match(self.today + relativedelta(days=3)))
        self.assertTrue(followup.is_match(self.today))
        self.assertFalse(followup.is_match(self.today + relativedelta(days=4)))

    def test_is_match_unknown_comparator(self):
        followup = self._create_followup()
        followup.match = False
        self.assertIsNone(followup.is_match(self.today))

    # ------------------------------------------------------------------
    # followup.send.wizard
    # ------------------------------------------------------------------
    def test_get_amount_residual(self):
        refund = self._create_move(self.other_customer, 30.0, self.today, 0, move_type="out_refund")
        company_currency = self._create_followup(use_customer_currency=False)
        customer_currency = self._create_followup(use_customer_currency=True)
        self.assertEqual(self.wizard.get_amount_residual(company_currency, self.invoice), 100.0)
        self.assertEqual(self.wizard.get_amount_residual(company_currency, refund), -30.0)
        self.assertEqual(self.wizard.get_amount_residual(customer_currency, self.invoice), 100.0)
        self.assertEqual(self.wizard.get_amount_residual(customer_currency, refund), -30.0)

    def test_run_followup_sends_mail(self):
        self._create_followup()
        self.wizard.run_followup()
        mails = self._mails()
        self.assertEqual(len(mails), 1)
        body = mails.body_html
        self.assertIn("Followup Customer", body)
        self.assertIn(f"INV:{self.invoice.name}", body)
        self.assertIn("100.00", body)
        self.assertIn(self.invoice.currency_id.name, body)
        self.assertNotIn("[invoices]", body)
        self.assertNotIn("$total_due_debit", body)
        self.assertNotIn(self.override_partner, mails.recipient_ids)

    def test_run_followup_selected_codes(self):
        self._create_followup(code="F5")
        self.wizard.run_followup(["OTHER"])
        self.assertFalse(self._mails())
        self.wizard.run_followup(["F5"])
        self.assertEqual(len(self._mails()), 1)

    def test_run_followup_no_followups(self):
        self.wizard.run_followup()
        self.assertFalse(self._mails())

    def test_run_followup_no_matching_invoice(self):
        self._create_followup(relative_days=1)
        self.wizard.run_followup()
        self.assertFalse(self._mails())

    def test_run_followup_within_margin(self):
        self._create_followup(amount_margin=1000.0)
        messages_before = self.customer.message_ids
        self.wizard.run_followup()
        self.assertFalse(self._mails())
        new_messages = self.customer.message_ids - messages_before
        self.assertTrue(any("Followup not sent" in (m.body or "") for m in new_messages))

    def test_run_followup_invoice_date_with_refunds_customer_currency(self):
        self._create_move(self.customer, 40.0, self.today - relativedelta(days=2), 1, move_type="out_refund")
        self._create_followup(
            date_field="Invoice date",
            relative_days=10,
            match=">=",
            with_refunds=True,
            only_open=False,
            use_customer_currency=True,
        )
        self.wizard.run_followup()
        mails = self._mails()
        self.assertEqual(len(mails), 1)
        # only the invoice matches the invoice date rule (10 days ago), due total = 100 - 40
        self.assertIn(f"INV:{self.invoice.name}", mails.body_html)
        self.assertIn("60.00", mails.body_html)

    def test_run_followup_override_partner(self):
        self.env["ir.config_parameter"].sudo().set_param("followup.override_partner_id", str(self.override_partner.id))
        self._create_followup()
        self.wizard.run_followup()
        mails = self._mails()
        self.assertEqual(len(mails), 1)
        self.assertIn(self.override_partner, mails.recipient_ids)

    def test_run_followup_override_partner_invalid(self):
        self.env["ir.config_parameter"].sudo().set_param("followup.override_partner_id", "'not-an-id'")
        self._create_followup()
        self.wizard.run_followup()
        mails = self._mails()
        self.assertEqual(len(mails), 1)
        self.assertNotIn(self.override_partner, mails.recipient_ids)

    def test_send_now(self):
        followup = self._create_followup()
        followup.send_now()
        self.assertEqual(len(self._mails()), 1)
