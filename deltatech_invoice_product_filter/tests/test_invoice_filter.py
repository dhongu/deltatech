from odoo.tests.common import TransactionCase


class TestAccountInvoiceView(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create necessary records for the test
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

        self.journal = self.env["account.journal"].create(
            {
                "name": "Test Journal",
                "type": "general",
                "code": "TJ",
                "company_id": self.company.id,
            }
        )

        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "consu",
                "company_id": self.company.id,
            }
        )

        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "company_id": self.company.id,
            }
        )

        self.account = self.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "TEST",
                "company_id": self.company.id,
            }
        )

        self.invoice_a = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "journal_id": self.journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1,
                            "name": "Test A",
                            "price_unit": 1.0,
                            "account_id": self.account.id,
                        },
                    )
                ],
            }
        )

    def test_product_filter(self):
        # Use the product filter to search for invoices
        invoices = self.env["account.move"].search([("line_ids.product_id", "ilike", "Test A")])

        # Check that the correct invoice was found
        self.assertEqual(invoices, self.invoice_a)
