from datetime import timedelta

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInvoiceNumber(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_sale"]
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

    def test_change_posted_invoice_number(self):
        invoice = self._create_invoice()
        invoice.action_post()
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

    def test_restrict_invoice_date(self):
        today = fields.Date.today()
        self.journal.restrict_date = True
        later_invoice = self._create_invoice(today)
        later_invoice.action_post()
        earlier_invoice = self._create_invoice(today - timedelta(days=1))

        result = earlier_invoice.action_post()

        self.assertFalse(result)
        self.assertEqual(earlier_invoice.state, "draft")
