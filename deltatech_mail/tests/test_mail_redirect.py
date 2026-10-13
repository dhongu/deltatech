# ©  2026 Terrabit
# See README.rst file on addons root folder for license details


from odoo import tools
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.mail.tests.common import MailCommon


@tagged("post_install", "-at_install", "deltatech_mail")
class TestMailRedirect(MailCommon):
    """MAIL-001: substitutions and the company sender option must reach the
    Odoo 19 outgoing flow (``send`` / ``_prepare_outgoing_list``)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["mail.substitution"].search([]).unlink()
        cls.env["ir.config_parameter"].set_param("mail.use_company_email", False)
        cls.customer = cls.env["res.partner"].create({"name": "Customer", "email": "customer@example.com"})

    def _create_mail(self, **values):
        vals = {
            "subject": "Test",
            "body_html": "<p>Test</p>",
            "email_from": "sender@example.com",
            "model": "res.partner",
            "res_id": self.customer.id,
            "email_to": "original.to@example.com",
            "email_cc": "original.cc@example.com",
            "recipient_ids": [(4, self.customer.id)],
        }
        vals.update(values)
        return self.env["mail.mail"].sudo().create(vals)

    def _sent_addresses(self):
        addresses = []
        for sent in self._mails:
            addresses += sent["email_to"] + (sent.get("email_cc") or [])
        return " ".join(addresses)

    def test_no_substitution_keeps_recipients(self):
        mail = self._create_mail()
        with self.mock_mail_gateway():
            mail.send()
        sent = self._sent_addresses()
        self.assertIn("original.to@example.com", sent)
        self.assertIn("customer@example.com", sent)

    def test_receiver_substitution_redirects_queued_mail(self):
        self.env["mail.substitution"].create(
            {"name": "res.partner", "email": "redirect@example.com", "type": "receiver"}
        )
        mail = self._create_mail()
        with self.mock_mail_gateway():
            mail.send()
        self.assertTrue(self._mails)
        for sent in self._mails:
            self.assertEqual(sent["email_to"], ["redirect@example.com"])
            self.assertFalse(sent.get("email_cc"))
        self.assertEqual(mail.state, "sent")

    def test_receiver_substitution_other_model_ignored(self):
        self.env["mail.substitution"].create(
            {"name": "sale.order", "email": "redirect@example.com", "type": "receiver"}
        )
        mail = self._create_mail()
        with self.mock_mail_gateway():
            mail.send()
        self.assertNotIn("redirect@example.com", self._sent_addresses())

    def test_sender_substitution(self):
        self.env["mail.substitution"].create({"name": False, "email": "noreply@example.com", "type": "sender"})
        mail = self._create_mail()
        with self.mock_mail_gateway():
            mail.send()
        self.assertTrue(self._mails)
        for sent in self._mails:
            self.assertEqual(sent["email_from"], "noreply@example.com")
            # a sender substitution must not become a recipient
            self.assertNotIn("noreply@example.com", sent["email_to"])

    def test_company_email_on_send(self):
        self.env["ir.config_parameter"].set_param("mail.use_company_email", True)
        mail = self._create_mail(author_id=self.partner_employee.id)
        with self.mock_mail_gateway():
            mail.send()
        company = self.user_employee.company_id
        expected = tools.formataddr((company.name, company.email))
        self.assertTrue(self._mails)
        for sent in self._mails:
            self.assertEqual(sent["email_from"], expected)

    def test_company_email_on_message_post(self):
        self.env["ir.config_parameter"].set_param("mail.use_company_email", True)
        company = self.user_employee.company_id
        message = self.customer.with_user(self.user_employee).message_post(body="Hello")
        self.assertEqual(message.email_from, tools.formataddr((company.name, company.email)))

    def test_company_email_option_off(self):
        message = self.customer.with_user(self.user_employee).message_post(body="Hello")
        self.assertEqual(message.email_from, self.partner_employee.email_formatted)

    def test_company_email_missing_raises(self):
        self.env["ir.config_parameter"].set_param("mail.use_company_email", True)
        self.user_employee.company_id.email = False
        with self.assertRaises(UserError):
            self.customer.with_user(self.user_employee).message_post(body="Hello")
