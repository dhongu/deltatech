# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from odoo.addons.mail.models.mail_thread import MailThread
from odoo.addons.mail.tests.common import MailCommon


@tagged("post_install", "-at_install", "deltatech_mail")
class TestMailSubstitutionAccess(MailCommon):
    """MAILSUB-001 (#3540): only administrators configure the substitutions,
    which apply to the emails and messages of every user."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["mail.substitution"].search([]).unlink()
        cls.env["mail.body.substitution"].search([]).unlink()
        cls.substitution = cls.env["mail.substitution"].create(
            {"name": False, "email": "admin-redirect@example.com", "type": "receiver"}
        )
        cls.body_substitution = cls.env["mail.body.substitution"].create(
            {"body_part": "<p>OLD</p>", "substitution": "<p>NEW</p>"}
        )
        cls.portal_user = new_test_user(cls.env, login="mailsub_portal", groups="base.group_portal")
        cls.customer = cls.env["res.partner"].create({"name": "Customer", "email": "customer@example.com"})

    def test_employee_cannot_create_substitution(self):
        with self.assertRaises(AccessError):
            self.env["mail.substitution"].with_user(self.user_employee).create(
                {"name": False, "email": "attacker@example.com", "type": "receiver"}
            )

    def test_employee_cannot_write_substitution(self):
        with self.assertRaises(AccessError):
            self.substitution.with_user(self.user_employee).write({"email": "attacker@example.com"})

    def test_employee_cannot_create_body_substitution(self):
        with self.assertRaises(AccessError):
            self.env["mail.body.substitution"].with_user(self.user_employee).create(
                {"body_part": "<p>Hello</p>", "substitution": "<p>Injected</p>"}
            )

    def test_employee_cannot_write_body_substitution(self):
        with self.assertRaises(AccessError):
            self.body_substitution.with_user(self.user_employee).write({"substitution": "<p>Injected</p>"})

    def test_employee_can_read_substitutions(self):
        self.assertTrue(self.env["mail.substitution"].with_user(self.user_employee).search([]))
        self.assertTrue(self.env["mail.body.substitution"].with_user(self.user_employee).search([]))

    def test_admin_can_manage_substitutions(self):
        sub = (
            self.env["mail.substitution"]
            .with_user(self.user_admin)
            .create({"name": "res.partner", "email": "other@example.com", "type": "receiver"})
        )
        sub.write({"email": "changed@example.com"})
        sub.unlink()

    def test_employee_post_applies_body_substitution(self):
        message = self.customer.with_user(self.user_employee).message_post(body="<p>OLD</p>")
        self.assertIn("NEW", str(message.body))

    def test_portal_post_applies_body_substitution(self):
        # the portal author has no access to the rules: message_post reads them
        # with sudo; the standard posting (document access) is out of scope here
        received = {}

        def fake_message_post(records, body="", **kwargs):
            received["body"] = body
            return records.env["mail.message"]

        partner = self.portal_user.partner_id.with_user(self.portal_user)
        with patch.object(MailThread, "message_post", fake_message_post):
            partner.message_post(body="<p>OLD</p>")
        self.assertIn("NEW", str(received["body"]))
