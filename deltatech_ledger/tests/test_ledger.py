# ©  2024 YourCompany
#              Your Name <your_email@example.com>
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestLedger(TransactionCase):

    def test_create_ledger_entry(self):
        Ledger = self.env["ledger.ledger"]

        # Create a ledger record with entry type
        vals = {
            "record_type": "entry",
            "record_short_description": "Test Entry",
        }
        ledger_entry = Ledger.create(vals)

        # Assertions
        self.assertEqual(ledger_entry.state, "active")
        self.assertEqual(ledger_entry.record_type, "entry")

    def test_create_ledger_exit(self):
        Ledger = self.env["ledger.ledger"]

        # Create a ledger record with exit type
        vals = {
            "record_type": "exit",
            "record_short_description": "Test Exit",
        }
        ledger_exit = Ledger.create(vals)

        # Assertions
        self.assertEqual(ledger_exit.state, "active")
        self.assertEqual(ledger_exit.record_type, "exit")
        self.assertEqual(ledger_exit.document_number, ledger_exit.name)

    def test_cancel_ledger(self):
        Ledger = self.env["ledger.ledger"]

        # Create a ledger record
        vals = {
            "record_type": "entry",
            "record_short_description": "To be canceled",
        }
        ledger_record = Ledger.create(vals)

        # Cancel the ledger record
        ledger_record.button_cancel()

        # Assertions
        self.assertEqual(ledger_record.state, "canceled")
