from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleFeedback(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a.email = "partner_a@example.com"
        cls.invoice = cls._create_invoice(
            partner_id=cls.partner_a,
            invoice_date=date.today() + relativedelta(days=-3),
            invoice_line_ids=[cls._prepare_invoice_line(product_id=cls.product_a)],
            post=True,
        )

    def _feedback_ratings(self):
        return self.env["rating.rating"].search(
            [("res_model", "=", "product.template"), ("res_id", "=", self.product_a.product_tmpl_id.id)]
        )

    def test_request_feedback(self):
        self.company_data["company"].website = "https://shop.example.com"
        messages_before = self.invoice.message_ids
        self.invoice.request_feedback()
        message = self.invoice.message_ids - messages_before
        self.assertEqual(len(message), 1)
        self.assertEqual(message.subject, f"{self.company_data['company'].name} (Ref {self.invoice.name})")
        rating = self._feedback_ratings()
        self.assertEqual(len(rating), 1)
        self.assertEqual(rating.partner_id, self.partner_a)
        self.assertIn(f"https://shop.example.com/rate/{rating.access_token}/5", message.body)
        self.assertIn(self.partner_a, message.partner_ids)

    def test_cron_request_feedback(self):
        company = self.company_data["company"]
        self.env["ir.config_parameter"].sudo().set_int("sale.days_request_feedback", 3)
        self.env["account.move"].cron_request_feedback()
        self.assertFalse(self._feedback_ratings(), "Feedback is not requested while disabled on the company")
        company.sale_feedback = True
        self.env["account.move"].cron_request_feedback()
        self.assertEqual(len(self._feedback_ratings()), 1)
