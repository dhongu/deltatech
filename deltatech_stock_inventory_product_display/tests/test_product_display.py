# ©  2024 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductDisplay(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "list_price": 100.0,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

    def test_sale_order_action_view_products(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        action = sale_order.action_view_products()
        self.assertEqual(action["domain"], [("id", "in", [self.product.product_tmpl_id.id])])
        self.assertTrue(action.get("context", {}).get("display_free_quantity"))

    def test_account_move_action_view_products(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        action = invoice.action_view_products()
        self.assertEqual(action["domain"], [("id", "in", [self.product.product_tmpl_id.id])])
