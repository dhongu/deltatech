# ©  2024 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "deltatech_mail")
class TestMailSubstitution(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Partner", "email": "partner@example.com"})

    def test_mail_substitution_create(self):
        sub = self.env["mail.substitution"].create(
            {
                "name": "res.partner",
                "email": "redirect@example.com",
                "type": "receiver",
            }
        )
        self.assertEqual(sub.name, "res.partner")
        self.assertEqual(sub.email, "redirect@example.com")
        self.assertEqual(sub.type, "receiver")

    def test_mail_substitution_default_type(self):
        sub = self.env["mail.substitution"].create(
            {
                "name": False,
                "email": "default@example.com",
            }
        )
        self.assertEqual(sub.type, "receiver")

    def test_mail_body_substitution_create(self):
        body_sub = self.env["mail.body.substitution"].create(
            {
                "name": "Test Body Sub",
                "body_part": "<p>Hello World</p>",
                "substitution": "<p>Hello Odoo</p>",
            }
        )
        self.assertEqual(body_sub.name, "Test Body Sub")

    def test_message_post_body_substitution(self):
        body_sub = self.env["mail.body.substitution"].create(
            {
                "name": "Replace Test",
                "body_part": "<p>Hello REPLACE_ME end</p>",
                "substitution": "<p>Hello REPLACED end</p>",
            }
        )
        msg = self.partner.message_post(body="<p>Hello REPLACE_ME end</p>")
        self.assertIn("REPLACED", msg.body)
        self.assertNotIn("REPLACE_ME", msg.body)
        body_sub.unlink()

    def test_message_post_no_body_substitution(self):
        # Ensure message_post works normally when no body substitutions exist
        self.env["mail.body.substitution"].search([]).unlink()
        msg = self.partner.message_post(body="Hello unchanged")
        self.assertIn("Hello unchanged", msg.body)

    def test_message_post_empty_body(self):
        # Empty body should not trigger substitution logic
        msg = self.partner.message_post(body="")
        self.assertFalse(msg.body)
