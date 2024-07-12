from odoo.tests.common import TransactionCase


class TestAccountInvoiceView(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create necessary records for the test
        self.product = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "consu",
            }
        )

        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        self.invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "name": "Test A",
                            "price_unit": 1.0,
                            "account_id": self.env["account.account"].search([], limit=1).id,
                        },
                    )
                ],
            }
        )

    def test_product_filter(self):
        # Use the product filter to search for invoices
        invoices = self.env["account.move"].search([("line_ids.product_id", "ilike", "Test A")])

        # Check that the correct invoice was found
        self.assertEqual(invoices, self.invoice)
