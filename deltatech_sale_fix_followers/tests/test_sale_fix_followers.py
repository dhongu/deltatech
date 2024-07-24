from odoo.tests.common import TransactionCase


class TestMailThread(TransactionCase):

    def setUp(self):
        super().setUp()

        # Setup test data
        self.partner_1 = self.env["res.partner"].create({"name": "Partner 1"})

        self.subtype_1 = self.env["mail.message.subtype"].create({"name": "Subtype 1"})

        self.mail_thread = self.env["mail.thread"]

    def test_message_subscribe(self):
        # Test subscribing a partner to a thread
        result = self.mail_thread.message_subscribe(partner_ids=[self.partner_1.id], subtype_ids=[self.subtype_1.id])
        self.assertTrue(result, "Failed to subscribe partner to thread")
