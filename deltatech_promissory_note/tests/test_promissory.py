# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.exceptions import UserError
from odoo.tests import Form, new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "promissory")
class TestPromissoryNote(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "TestA"})
        self.partner_b = self.env["res.partner"].create({"name": "TestB"})
        self.company_partner = self.env.company.partner_id
        # The form requires both banks (the note is printed with them).
        self.bank = self.env["res.bank"].create({"name": "TEST Bank", "bic": "TESTROBU"})

    def _new_note(self, note_type, partner):
        promissory_note = Form(self.env["promissory.note"])
        promissory_note.name = "Test"
        promissory_note.date_due = "2020-03-18"
        promissory_note.type = note_type
        if note_type == "vendor":
            promissory_note.beneficiary_id = partner
        else:
            promissory_note.issuer_id = partner
        promissory_note.amount = 1000
        promissory_note.currency_id = self.env.ref("base.EUR")
        promissory_note.acc_issuer = "XXX"
        promissory_note.acc_beneficiary = "XXX"
        promissory_note.bank_issuer_id = self.bank
        promissory_note.bank_beneficiary_id = self.bank
        promissory_note.is_last_bo = True
        return promissory_note.save()

    def test_promissory_note_vendor(self):
        """A vendor note is issued by the company to the supplier."""
        promissory_note = self._new_note("vendor", self.partner_b)
        self.assertEqual(promissory_note.issuer_id, self.company_partner)
        self.assertEqual(promissory_note.beneficiary_id, self.partner_b)

        promissory_note.action_cashed()
        self.assertEqual(promissory_note.state, "cashed")

    def test_promissory_note_customer(self):
        """A customer note is issued by the customer to the company."""
        promissory_note = self._new_note("customer", self.partner_a)
        self.assertEqual(promissory_note.issuer_id, self.partner_a)
        self.assertEqual(promissory_note.beneficiary_id, self.company_partner)

        promissory_note.action_cashed()
        self.assertEqual(promissory_note.state, "cashed")

        promissory_note.action_not_cashed()
        self.assertEqual(promissory_note.state, "not_cashed")
        promissory_note.action_cancel()
        self.assertEqual(promissory_note.state, "cancel")

    def test_last_note_cashed_notifies_bo_users(self):
        """Cashing the last note of an agreement notifies the users of the BO notifications group."""
        notified = new_test_user(
            self.env, login="test_bo_notified", groups="base.group_user,deltatech_promissory_note.bo_notifications"
        )
        not_notified = new_test_user(self.env, login="test_bo_other", groups="base.group_user")
        promissory_note = self._new_note("customer", self.partner_a)

        promissory_note.action_cashed()

        notification = promissory_note.message_ids.filtered(lambda message: "BO - the last" in (message.subject or ""))
        self.assertEqual(len(notification), 1)
        self.assertIn(notified.partner_id, notification.partner_ids)
        self.assertNotIn(not_notified.partner_id, notification.partner_ids)

    def test_amount_must_be_positive(self):
        with self.assertRaises(UserError):
            self._new_note("customer", self.partner_a).amount = 0
