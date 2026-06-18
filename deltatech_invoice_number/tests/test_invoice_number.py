from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInvoiceNumber(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_sale"]
        cls.product_a.standard_price = 0
        cls.partner_a.country_id = cls.env.ref("base.us")
        cls.env.ref("deltatech_invoice_number.group_change_invoice_number").user_ids = [Command.link(cls.env.user.id)]
        cls.sequence = cls.env["ir.sequence"].create(
            {
                "name": "Test invoice sequence",
                "prefix": "TEST/%(year)s/",
                "padding": 4,
            }
        )
        cls.journal.journal_sequence_id = cls.sequence

    def _create_invoice(self, invoice_date=None):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "journal_id": self.journal.id,
                "invoice_date": invoice_date or fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1,
                            "price_unit": 100,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )

    def test_action_get_number(self):
        invoice = self._create_invoice()

        self.assertTrue(invoice.action_get_number())

        self.assertRegex(invoice.name, r"^TEST/\d{4}/\d{4}$")

    def test_action_get_number_requires_invoice_date(self):
        invoice = self._create_invoice()
        invoice.invoice_date = False

        with self.assertRaisesRegex(UserError, "The invoice has no date"):
            invoice.action_get_number()

    def test_action_get_number_requires_journal_sequence(self):
        invoice = self._create_invoice()
        self.journal.journal_sequence_id = False

        with self.assertRaisesRegex(UserError, "Please define a sequence"):
            invoice.action_get_number()

    def test_action_get_number_respects_date_restriction(self):
        today = fields.Date.today()
        self.journal.restrict_date = True
        later_invoice = self._create_invoice(today)
        later_invoice.action_post()
        earlier_invoice = self._create_invoice(today - timedelta(days=1))

        with self.assertRaisesRegex(UserError, "Post the invoice"):
            earlier_invoice.action_get_number()

    def test_onchange_journal_warns_for_restricted_date(self):
        today = fields.Date.today()
        self.journal.restrict_date = True
        later_invoice = self._create_invoice(today)
        later_invoice.action_post()
        earlier_invoice = self._create_invoice(today - timedelta(days=1))

        result = earlier_invoice._onchange_journal_id()

        self.assertIn("Post the invoice", result["warning"]["message"])

    def test_change_posted_invoice_number(self):
        invoice = self._create_invoice()
        invoice.action_post()
        invoice.ref = "OLD-REFERENCE"
        invoice.line_ids.write({"ref": "OLD-REFERENCE"})
        new_number = f"TEST/{fields.Date.today().year}/9999"
        wizard = (
            self.env["account.invoice.change.number"]
            .with_context(
                active_id=invoice.id,
                active_model="account.move",
            )
            .create({"internal_number": new_number})
        )

        wizard.do_change_number()

        self.assertEqual(invoice.name, new_number)
        self.assertEqual(invoice.ref, new_number)
        self.assertTrue(all(line.ref == new_number for line in invoice.line_ids))

    def test_change_number_wizard_defaults_to_current_number(self):
        invoice = self._create_invoice()
        wizard_model = self.env["account.invoice.change.number"].with_context(active_id=invoice.id)

        defaults = wizard_model.default_get(["internal_number"])

        self.assertEqual(defaults["internal_number"], invoice.name)

    def test_change_number_wizard_without_active_invoice_closes(self):
        wizard = self.env["account.invoice.change.number"].create({"internal_number": "TEST/EMPTY"})

        action = wizard.do_change_number()

        self.assertEqual(action, {"type": "ir.actions.act_window_close"})

    def test_restrict_invoice_date(self):
        today = fields.Date.today()
        self.journal.restrict_date = True
        later_invoice = self._create_invoice(today)
        later_invoice.action_post()
        earlier_invoice = self._create_invoice(today - timedelta(days=1))

        with self.assertRaisesRegex(UserError, "Post the invoice"):
            earlier_invoice.action_post()
        self.assertEqual(earlier_invoice.state, "draft")
