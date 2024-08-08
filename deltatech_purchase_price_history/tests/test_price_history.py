# ©  2024-now Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests.common import TransactionCase


class TestPurchasePriceHistory(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "detailed_type": "service",
            }
        )

        self.invoice_a = self.env["account.move"].create(
            [
                {
                    "move_type": "in_invoice",
                    "partner_id": self.partner_a.id,
                    "invoice_date": fields.Date.today(),
                    # "currency_id": cls.currency.id,
                    # "journal_id": cls.journal.id,
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "product_id": self.product_a.id,
                                "name": "Test sale",
                                "quantity": 1,
                                "price_unit": 10.00,
                            },
                        ),
                    ],
                }
            ]
        )
        self.invoice_b = self.env["account.move"].create(
            [
                {
                    "move_type": "in_invoice",
                    "partner_id": self.partner_a.id,
                    "invoice_date": fields.Date.today(),
                    # "currency_id": cls.currency.id,
                    # "journal_id": cls.journal.id,
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "product_id": self.product_a.id,
                                "name": "Test sale",
                                "quantity": 1,
                                "price_unit": 20.00,
                            },
                        ),
                    ],
                }
            ]
        )
        self.invoice_a.action_post()
        self.invoice_b.action_post()

    def test_product_purchase_prices(self):
        # cannot check further, operations not commited
        self.product_a.product_tmpl_id.compute_purchase_history()
