# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseOrderCreateBill(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_vendor = self.env["res.partner"].create({"name": "Vendor"})
        self.product = self.env["product.product"].create({"name": "Product", "type": "consu"})

        self.purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_vendor.id,
                "partner_ref": "GRW0003",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        self.purchase_order.button_confirm()

    def test_prepare_invoice_copies_vendor_reference(self):
        invoice_vals = self.purchase_order._prepare_invoice()
        self.assertEqual(invoice_vals["ref"], "GRW0003")
        self.assertEqual(invoice_vals["payment_reference"], "GRW0003")

    def test_prepare_invoice_without_vendor_reference(self):
        self.purchase_order.partner_ref = False
        invoice_vals = self.purchase_order._prepare_invoice()
        self.assertEqual(invoice_vals["ref"], "")
        self.assertEqual(invoice_vals["payment_reference"], "")

    def _make_order(self, qty=1.0, price=100.0):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": qty,
                            "price_unit": price,
                        },
                    )
                ],
            }
        )
        order.button_confirm()
        return order

    def test_create_bills_button_in_list_header(self):
        """The list view used by the RFQ/purchase order menu offers "Create Bills"."""
        view = self.env.ref("purchase.purchase_order_kpis_tree")
        arch = self.env["purchase.order"].get_view(view.id, "list")["arch"]
        self.assertIn('name="action_create_invoice"', arch)

    def test_create_bill_button_in_form(self):
        view = self.env.ref("purchase.purchase_order_form")
        arch = self.env["purchase.order"].get_view(view.id, "form")["arch"]
        self.assertIn('name="action_create_invoice"', arch)

    def test_create_bills_from_several_orders_returns_one_credit_note(self):
        """Two returned orders billed together give a single vendor credit note."""
        self.product.purchase_method = "purchase"
        orders = self._make_order(qty=2.0) | self._make_order(qty=3.0)
        orders.action_create_invoice()
        bills = orders.invoice_ids
        self.assertEqual(len(bills), 1)
        bills.invoice_date = fields.Date.context_today(bills)
        bills.action_post()

        # the goods go back to the vendor: the ordered quantities drop below what
        # was already invoiced, so both orders are left with a negative quantity
        for order in orders:
            order.order_line.product_qty = 0.0
        self.assertEqual(set(orders.mapped("invoice_status")), {"to invoice"})

        orders.action_create_invoice()
        storno = orders.invoice_ids - bills
        self.assertEqual(len(storno), 1)
        self.assertEqual(storno.move_type, "in_refund")
        self.assertEqual(storno.amount_untaxed, 500.0)

    def test_create_bills_from_several_orders_keeps_all_vendor_references(self):
        """A bill grouping several orders keeps every vendor reference."""
        self.product.purchase_method = "purchase"
        order_a = self._make_order()
        order_a.partner_ref = "REF-A"
        order_b = self._make_order()
        order_b.partner_ref = "REF-B"
        order_c = self._make_order()
        order_c.partner_ref = "REF-A"
        orders = order_a | order_b | order_c
        orders.action_create_invoice()
        bill = orders.invoice_ids
        self.assertEqual(len(bill), 1)
        self.assertEqual(bill.ref, "REF-A, REF-B")
        # several distinct references: no single payment reference can be right
        self.assertFalse(bill.payment_reference)

    def test_create_bills_from_several_orders_same_reference(self):
        self.product.purchase_method = "purchase"
        orders = self._make_order() | self._make_order()
        orders.partner_ref = "REF-SAME"
        orders.action_create_invoice()
        bill = orders.invoice_ids
        self.assertEqual(len(bill), 1)
        self.assertEqual(bill.ref, "REF-SAME")
        self.assertEqual(bill.payment_reference, "REF-SAME")

    def test_bill_skips_backordered_line(self):
        if "stock.picking" not in self.env:
            self.skipTest("stock is not installed")
        product2 = self.env["product.product"].create(
            {"name": "Product 2", "type": "consu", "is_storable": True, "purchase_method": "receive"}
        )
        self.product.write({"is_storable": True, "purchase_method": "receive"})
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_vendor.id,
                "order_line": [
                    (0, 0, {"product_id": prod.id, "product_qty": 5.0, "price_unit": 10.0})
                    for prod in (self.product, product2)
                ],
            }
        )
        order.button_confirm()
        picking = order.picking_ids
        picking.move_ids[0].quantity = 5.0
        picking.move_ids[1].quantity = 0.0
        picking.with_context(skip_backorder=True, picking_ids_not_to_backorder=[]).button_validate()
        received = order.order_line.filtered(lambda line: line.qty_received)
        action = order.action_create_invoice()
        bill = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(bill.invoice_line_ids.purchase_line_id, received)
        self.assertEqual(bill.invoice_line_ids.quantity, 5.0)

    def test_bill_nothing_to_invoice(self):
        if "stock.picking" not in self.env:
            self.skipTest("stock is not installed")
        product2 = self.env["product.product"].create(
            {"name": "Product 2", "type": "consu", "is_storable": True, "purchase_method": "receive"}
        )
        self.product.write({"is_storable": True, "purchase_method": "receive"})
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_vendor.id,
                "order_line": [(0, 0, {"product_id": product2.id, "product_qty": 5.0, "price_unit": 10.0})],
            }
        )
        order.button_confirm()
        with self.assertRaises(UserError):
            order.action_create_invoice()

    def _stock_products(self, count=2):
        if "stock.picking" not in self.env:
            self.skipTest("stock is not installed")
        return self.env["product.product"].create(
            [
                {"name": f"Stock {i}", "type": "consu", "is_storable": True, "purchase_method": "receive"}
                for i in range(count)
            ]
        )

    def _receive_only(self, order, product):
        picking = order.picking_ids
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty if move.product_id == product else 0.0
        picking.with_context(skip_backorder=True, picking_ids_not_to_backorder=[]).button_validate()

    def test_bill_removes_orphan_sections_and_notes(self):
        prod_a, prod_b = self._stock_products()
        section = {"display_type": "line_section", "name": "Section", "product_qty": 0.0}
        note = {"display_type": "line_note", "name": "Note", "product_qty": 0.0}
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_vendor.id,
                "order_line": [
                    (0, 0, section | {"name": "S1"}),
                    (0, 0, note | {"name": "N1"}),
                    (0, 0, {"product_id": prod_a.id, "product_qty": 5.0, "price_unit": 10.0}),
                    (0, 0, section | {"name": "S2"}),
                    (0, 0, note | {"name": "N2"}),
                    (0, 0, {"product_id": prod_b.id, "product_qty": 5.0, "price_unit": 10.0}),
                ],
            }
        )
        order.button_confirm()
        self._receive_only(order, prod_b)
        bill = self.env["account.move"].browse(order.action_create_invoice()["res_id"])
        self.assertEqual(
            bill.invoice_line_ids.sorted("sequence").mapped("name"),
            ["S2", "N2", bill.invoice_line_ids.filtered("product_id").name],
        )

    def test_no_empty_bill_for_other_vendor(self):
        prod_a, prod_b = self._stock_products()
        other_vendor = self.env["res.partner"].create({"name": "Other Vendor"})
        orders = self.env["purchase.order"]
        for partner, product in ((other_vendor, prod_a), (self.partner_vendor, prod_b)):
            orders |= self.env["purchase.order"].create(
                {
                    "partner_id": partner.id,
                    "order_line": [(0, 0, {"product_id": product.id, "product_qty": 5.0, "price_unit": 10.0})],
                }
            )
        orders.button_confirm()
        self._receive_only(orders[1], prod_b)
        orders.action_create_invoice()
        self.assertFalse(orders[0].invoice_ids)
        self.assertEqual(len(orders[1].invoice_ids), 1)
