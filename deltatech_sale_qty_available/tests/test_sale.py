# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": cls.partner_a.id})]
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Test A",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Test B",
                "is_storable": True,
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        cls.product_c = cls.env["product.product"].create(
            {
                "name": "Test C (no stock)",
                "is_storable": True,
                "list_price": 10,
            }
        )

        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"]._update_available_quantity(cls.product_a, cls.stock_location, 1000)
        cls.env["stock.quant"]._update_available_quantity(cls.product_b, cls.stock_location, 1000)

    def _create_so(self, lines, picking_policy="direct"):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a
        so.picking_policy = picking_policy
        for product, qty in lines:
            with so.order_line.new() as so_line:
                so_line.product_id = product
                so_line.product_uom_qty = qty
        return so.save()

    def _deliver(self, so):
        picking = so.picking_ids
        picking.action_assign()
        for move in picking.move_ids:
            if move.product_uom_qty > 0 and move.quantity == 0:
                move.write({"quantity": move.product_uom_qty})
        picking._action_done()
        return picking

    def test_sale_picking_policy_direct(self):
        so = self._create_so([(self.product_a, 100), (self.product_b, 10)], "direct")
        so._compute_is_ready()
        self.assertTrue(so.is_ready)

        so.action_confirm()
        so._compute_is_ready()
        self.assertTrue(so.is_ready, "Moves are reserved, the order is ready")

        self._deliver(so)
        so._compute_is_ready()

        invoice = so._create_invoices()
        invoice = Form(invoice).save()
        self.assertTrue(invoice)

    def test_sale_picking_policy_one(self):
        so = self._create_so([(self.product_a, 100), (self.product_b, 10)], "one")
        so._compute_is_ready()
        self.assertTrue(so.is_ready)

        so.action_confirm()
        so._compute_is_ready()
        self.assertTrue(so.is_ready)

        self._deliver(so)
        so._compute_is_ready()

        invoice = so._create_invoices()
        invoice = Form(invoice).save()
        self.assertTrue(invoice)

    def test_quotation_not_ready_without_stock(self):
        # "one": all lines must be available
        so_one = self._create_so([(self.product_a, 10), (self.product_c, 5)], "one")
        so_one._compute_is_ready()
        self.assertFalse(so_one.is_ready)

        # "direct": one available line is enough
        so_direct = self._create_so([(self.product_a, 10), (self.product_c, 5)], "direct")
        so_direct._compute_is_ready()
        self.assertTrue(so_direct.is_ready)

        so_none = self._create_so([(self.product_c, 5)], "direct")
        so_none._compute_is_ready()
        self.assertFalse(so_none.is_ready)

    def test_cancelled_order_not_ready(self):
        so = self._create_so([(self.product_a, 10)])
        so._action_cancel()
        so._compute_is_ready()
        self.assertFalse(so.is_ready)

    def test_sale_search_search_is_ready(self):
        ready = self._create_so([(self.product_a, 10)])
        not_ready = self._create_so([(self.product_c, 5)])
        (ready | not_ready)._compute_is_ready()

        found = self.env["sale.order"].search([("is_ready", "=", True)])
        self.assertIn(ready, found)
        self.assertNotIn(not_ready, found)

        for domain in ([("is_ready", "=", False)], [("is_ready", "!=", True)]):
            found = self.env["sale.order"].search(domain)
            self.assertIn(not_ready, found)
            self.assertNotIn(ready, found)

    def test_qty_available_text(self):
        so = self._create_so([(self.product_a, 10), (self.product_c, 5)])
        line_a = so.order_line.filtered(lambda line: line.product_id == self.product_a)
        line_c = so.order_line.filtered(lambda line: line.product_id == self.product_c)
        self.assertIn("1000.0", line_a.qty_available_text)
        self.assertEqual(line_c.qty_available_text, "N/A")

    def test_order_form_view(self):
        arch = self.env["sale.order"].get_view(self.env.ref("sale.view_order_form").id, "form")["arch"]
        self.assertIn('name="qty_available_text"', arch)
