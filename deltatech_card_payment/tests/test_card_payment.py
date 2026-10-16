from odoo.tests.common import TransactionCase


class TestAccountPaymentMethod(TransactionCase):
    def setUp(self):
        super().setUp()

        # Search for the 'Card' payment method
        self.payment_method = self.env["account.payment.method"].search([("code", "=", "card_payment")], limit=1)
        assert self.payment_method, "Card payment method not found"

    def test_check_payment_method(self):
        # Check if the payment method is correctly set
        self.assertEqual(self.payment_method.name, "Card Payment", "Name is not correctly set")
        self.assertEqual(self.payment_method.code, "card_payment", "Code is not correctly set")
        self.assertEqual(self.payment_method.payment_type, "inbound", "Payment type is not correctly set")

    def test_get_payment_method_information(self):
        # Check the _get_payment_method_information method
        info = self.payment_method._get_payment_method_information()
        self.assertIn("card_payment", info, "_get_payment_method_information does not return correct information")

    def test_new_bank_journal_gets_card_payment_line(self):
        journal = self.env["account.journal"].create({"name": "Card Bank", "type": "bank", "code": "CRDB"})
        self.assertIn(self.payment_method, journal.inbound_payment_method_line_ids.payment_method_id)
        # the standard manual method is kept next to the card one
        manual = self.env.ref("account.account_payment_method_manual_in")
        self.assertIn(manual, journal.inbound_payment_method_line_ids.payment_method_id)

    def test_card_payment_available_on_bank_journal(self):
        journal = self.env["account.journal"].create({"name": "Card Bank 2", "type": "bank", "code": "CRDC"})
        self.assertIn(self.payment_method, journal.available_payment_method_ids)
