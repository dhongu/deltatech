"""
Tests for creating/viewing Purchase Orders directly from Sale Orders.
"""

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSalePurchaseOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "customer_rank": 1,
            }
        )
        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Test Vendor",
                "supplier_rank": 1,
            }
        )
        # Purchasable product
        cls.product_buy = cls.env["product.product"].create(
            {
                "name": "Buyable Product",
                "uom_id": cls.uom_unit.id,
                "purchase_ok": True,
                "list_price": 100.0,
            }
        )
        # Non-purchasable product
        cls.product_not_buy = cls.env["product.product"].create(
            {
                "name": "Non-Buyable Product",
                "uom_id": cls.uom_unit.id,
                "purchase_ok": False,
                "list_price": 50.0,
            }
        )

    def _create_sale_order(self, lines):
        order_lines = [
            Command.create(
                {
                    "product_id": product.id,
                    "product_uom_qty": qty,
                    "product_uom_id": self.uom_unit.id,
                    "price_unit": product.list_price,
                }
            )
            for product, qty in lines
        ]
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": order_lines,
            }
        )

    def test_action_create_purchase_order_prefills_lines(self):
        so = self._create_sale_order([(self.product_buy, 3)])

        action = so.action_create_rfq()

        # Validate action opens purchase order form in create mode with defaults
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("view_mode"), "form")
        ctx = action.get("context") or {}
        self.assertEqual(ctx.get("default_origin"), so.name)
        self.assertEqual(ctx.get("default_quote_id"), so.id)
        order_line_defaults = ctx.get("default_order_line") or []
        self.assertEqual(len(order_line_defaults), 1)
        # each default line is a (0, 0, values) triplet
        self.assertEqual(order_line_defaults[0][2]["product_id"], self.product_buy.id)
        self.assertEqual(order_line_defaults[0][2]["product_qty"], 3)

    def test_action_create_purchase_order_no_eligible_lines(self):
        so = self._create_sale_order([(self.product_not_buy, 2)])
        with self.assertRaises(UserError):
            so.action_create_rfq()

    def test_action_create_purchase_order_no_lines(self):
        so = self._create_sale_order([])
        with self.assertRaises(UserError):
            so.action_create_rfq()

    def test_action_view_purchase_orders_single_opens_form(self):
        so = self._create_sale_order([(self.product_buy, 1)])
        # Manually create a draft PO linked to the SO (vendor chosen manually)
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "quote_id": so.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_buy.id,
                            "product_qty": 1,
                            "uom_id": self.uom_unit.id,
                            "price_unit": 0.0,
                        }
                    )
                ],
            }
        )

        action = so.action_view_rfq()
        self.assertIsInstance(action, dict)
        # When only one PO exists, open its form directly
        self.assertEqual(action.get("res_id"), po.id)
        self.assertIn("form", (action.get("view_mode") or ""))

    def test_create_rfq_from_action_links_quote(self):
        so = self._create_sale_order([(self.product_buy, 4), (self.product_not_buy, 2)])
        action = so.action_create_rfq()
        lines = action["context"]["default_order_line"]
        self.assertEqual(len(lines), 1, "Only purchasable products are proposed")
        self.assertEqual(lines[0][2]["uom_id"], self.uom_unit.id)

        po = self.env["purchase.order"].with_context(**action["context"]).create({"partner_id": self.vendor.id})
        self.assertEqual(po.quote_id, so)
        self.assertEqual(po.origin, so.name)
        self.assertEqual(po.order_line.product_id, self.product_buy)
        self.assertEqual(po.order_line.product_qty, 4)
        self.assertEqual(po.order_line.uom_id, self.uom_unit)
        self.assertEqual(so.rfq_ids, po)
        self.assertEqual(so.rfq_count, 1)

    def test_action_view_rfq_multiple_opens_list(self):
        so = self._create_sale_order([(self.product_buy, 1)])
        pos = self.env["purchase.order"].create([{"partner_id": self.vendor.id, "quote_id": so.id} for _i in range(2)])
        self.assertEqual(so.rfq_count, 2)
        action = so.action_view_rfq()
        self.assertEqual(action["domain"], [("quote_id", "=", so.id)])
        self.assertFalse(action.get("res_id"))
        self.assertEqual(so.rfq_ids, pos)
