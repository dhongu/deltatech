from odoo.tests.common import TransactionCase


class TestAccountMoveLineColorTrigger(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create necessary records for testing
        self.product_product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )
        self.product_service = self.env["product.product"].create(
            {
                "name": "Test Service",
                "type": "service",
            }
        )

    def test_color_trigger_purchase_invoice_with_product_no_purchase_line(self):
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_product.id,
                            "price_unit": 100,
                            "quantity": 1,
                        },
                    )
                ],
            }
        )
        move._compute_color_trigger()
        self.assertTrue(move.color_triggered)
        self.assertEqual(move.line_ids[0].color_trigger, "danger")

    def test_color_trigger_sale_invoice_with_product_no_sale_line(self):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_product.id,
                            "price_unit": 100,
                            "quantity": 1,
                        },
                    )
                ],
            }
        )
        move._compute_color_trigger()
        self.assertTrue(move.color_triggered)
        self.assertEqual(move.line_ids[0].color_trigger, "danger")

    def test_color_trigger_purchase_invoice_no_product(self):
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": False,
                            "price_unit": 100,
                            "quantity": 1,
                        },
                    )
                ],
            }
        )
        move._compute_color_trigger()
        self.assertTrue(move.color_triggered)
        self.assertEqual(move.line_ids[0].color_trigger, "warning")

    def test_color_trigger_sale_invoice_no_product(self):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": False,
                            "price_unit": 100,
                            "quantity": 1,
                        },
                    )
                ],
            }
        )
        move._compute_color_trigger()
        self.assertTrue(move.color_triggered)
        self.assertEqual(move.line_ids[0].color_trigger, "warning")

    def test_color_trigger_other_invoice_type(self):
        account = self.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "TEST",
                "account_type": "income",
            }
        )
        move = self.env["account.move"].create(
            {
                "move_type": "entry",  # Not in ("in_invoice", "in_refund", "out_invoice", "out_refund")
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_product.id,
                            "account_id": account.id,
                            "name": "Test Line",
                            "price_unit": 100,
                            "quantity": 1,
                        },
                    )
                ],
            }
        )
        move._compute_color_trigger()
        self.assertFalse(move.color_triggered)
        self.assertFalse(move.line_ids[0].color_trigger)
