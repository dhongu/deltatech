# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleQtyAvailable(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.EUR").active = True

        country = cls.env.ref("base.ro")
        state = cls.env.ref("base.RO_B")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "country_id": country.id,
                "state_id": state.id,
                "city": "București",
                "street": "Str. Test 1",
                "zip": "010000",
            }
        )
        seller = [(0, 0, {"partner_id": cls.partner.id})]
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller,
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Product B",
                "is_storable": True,
                "standard_price": 70,
                "list_price": 120,
                "seller_ids": seller,
            }
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")

    def _add_stock(self, product, qty):
        self.env["stock.quant"]._update_available_quantity(product, self.stock_location, qty)

    def _make_order(self, lines, picking_policy="direct"):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner
        so.picking_policy = picking_policy
        for product, qty in lines:
            with so.order_line.new() as line:
                line.product_id = product
                line.product_uom_qty = qty
        return so.save()

    @staticmethod
    def _validate_picking(picking):
        picking.action_assign()
        for move in picking.move_ids:
            if move.product_uom_qty > 0 and move.quantity == 0:
                move.quantity = move.product_uom_qty
        picking._action_done()

    # --- draft/sent: stoc disponibil ---

    def test_draft_direct_policy_sufficient_stock(self):
        # Stock 1000 — comanda de 10 → ready
        self._add_stock(self.product_a, 1000)
        so = self._make_order([(self.product_a, 10)])
        self.assertTrue(so.is_ready, "Order should be ready when stock covers at least one line (direct policy)")

    def test_draft_direct_policy_no_stock(self):
        # Stoc 0 (initial) — comanda de 10 → not ready
        so = self._make_order([(self.product_a, 10)])
        self.assertFalse(so.is_ready, "Order should not be ready when stock is zero (direct policy)")

    def test_draft_direct_policy_partial_stock_one_line_covered(self):
        # Direct: suficient dacă CEL PUȚIN O linie e acoperită
        self._add_stock(self.product_a, 1000)
        # product_b rămâne la stoc 0
        so = self._make_order([(self.product_a, 10), (self.product_b, 5)])
        self.assertTrue(so.is_ready, "Order should be ready when at least one line has stock (direct policy)")

    def test_draft_one_policy_all_lines_covered(self):
        self._add_stock(self.product_a, 1000)
        self._add_stock(self.product_b, 1000)
        so = self._make_order([(self.product_a, 10), (self.product_b, 5)], picking_policy="one")
        self.assertTrue(so.is_ready, "Order should be ready when all lines are covered (one policy)")

    def test_draft_one_policy_partial_stock(self):
        # One: product_b rămâne la 0 → not ready
        self._add_stock(self.product_a, 1000)
        so = self._make_order([(self.product_a, 10), (self.product_b, 5)], picking_policy="one")
        self.assertFalse(so.is_ready, "Order should not be ready when one line has no stock (one policy)")

    # --- stare confirmată ---

    def test_confirmed_direct_with_reserved_moves(self):
        self._add_stock(self.product_a, 1000)
        so = self._make_order([(self.product_a, 10)])
        so.action_confirm()
        so.picking_ids.action_assign()
        self.assertTrue(so.is_ready, "Confirmed order with reserved moves should be ready (direct policy)")

    def test_confirmed_one_policy_fully_reserved(self):
        self._add_stock(self.product_a, 1000)
        self._add_stock(self.product_b, 1000)
        so = self._make_order([(self.product_a, 10), (self.product_b, 5)], picking_policy="one")
        so.action_confirm()
        so.picking_ids.action_assign()
        self.assertTrue(so.is_ready, "Confirmed order fully reserved should be ready (one policy)")

    def test_picking_done_not_yet_invoiced(self):
        self._add_stock(self.product_a, 1000)
        so = self._make_order([(self.product_a, 10)])
        so.action_confirm()
        self._validate_picking(so.picking_ids)
        self.assertTrue(so.is_ready, "Order with all pickings done but not invoiced should still be ready")

    def test_invoiced_order_not_ready(self):
        self._add_stock(self.product_a, 1000)
        so = self._make_order([(self.product_a, 10)])
        so.action_confirm()
        self._validate_picking(so.picking_ids)
        invoice = so._create_invoices()
        invoice.action_post()
        self.assertFalse(so.is_ready, "Invoiced order should not be ready")

    def test_cancelled_order_not_ready(self):
        so = self._make_order([(self.product_a, 10)])
        so.action_cancel()
        self.assertFalse(so.is_ready, "Cancelled order should not be ready")

    # --- search ---

    def test_search_is_ready_true(self):
        self._add_stock(self.product_a, 1000)
        so = self._make_order([(self.product_a, 10)])
        result = self.env["sale.order"].search([("is_ready", "=", True)])
        self.assertIn(so, result, "Ready order should appear in is_ready=True search")

    def test_search_is_ready_false(self):
        # Stoc 0 → not ready
        so = self._make_order([(self.product_a, 10)])
        result = self.env["sale.order"].search([("is_ready", "=", False)])
        self.assertIn(so, result, "Non-ready order should appear in is_ready=False search")
