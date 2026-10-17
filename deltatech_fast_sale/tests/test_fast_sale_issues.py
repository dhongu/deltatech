# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestFastSaleIssues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Fast Sale"})
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.product_a = cls.env["product.product"].create(
            {"name": "Fast A", "type": "consu", "is_storable": True, "list_price": 10}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Fast B", "type": "consu", "is_storable": True, "list_price": 20}
        )
        for product in cls.product_a | cls.product_b:
            cls.env["stock.quant"]._update_available_quantity(product, cls.warehouse.lot_stock_id, 100)

    def _create_order(self, products=None):
        products = products or (self.product_a | self.product_b)
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "order_line": [(0, 0, {"product_id": p.id, "product_uom_qty": 5}) for p in products],
            }
        )

    def test_notice_with_two_assigned_transfers(self):
        """#3388: the delivery notice must open the list when two transfers are assigned"""
        order = self._create_order()
        order.action_confirm()
        picking = order.picking_ids
        self.assertEqual(len(picking), 1)
        # move the second product in its own transfer of the same order
        second = picking.copy({"move_ids": [], "sale_id": order.id})
        picking.move_ids.filtered(lambda m: m.product_id == self.product_b).picking_id = second
        self.assertEqual(len(order.picking_ids), 2)

        action = order.action_button_confirm_notice()

        self.assertTrue(all(order.picking_ids.mapped("notice")))
        self.assertEqual(
            self.env["stock.picking"].search(action["domain"]),
            order.picking_ids,
        )

    def test_notice_with_one_assigned_transfer(self):
        order = self._create_order()
        order.action_confirm()
        action = order.action_button_confirm_notice()
        self.assertEqual(action["res_id"], order.picking_ids.id)
        self.assertTrue(order.picking_ids.notice)

    def test_confirm_to_invoice_two_step_delivery(self):
        """#3389: confirm, deliver and invoice must work in a two-step delivery warehouse"""
        self.warehouse.delivery_steps = "pick_ship"
        order = self._create_order()
        order.action_button_confirm_to_invoice()
        pickings = order.picking_ids
        self.assertGreaterEqual(len(pickings), 2)
        self.assertEqual(set(pickings.mapped("state")), {"done"})
        self.assertEqual(order.order_line.mapped("qty_delivered"), [5.0, 5.0])

    def test_confirm_to_invoice_three_step_delivery(self):
        self.warehouse.delivery_steps = "pick_pack_ship"
        order = self._create_order()
        order.action_button_confirm_to_invoice()
        self.assertGreaterEqual(len(order.picking_ids), 3)
        self.assertEqual(set(order.picking_ids.mapped("state")), {"done"})
        self.assertEqual(order.order_line.mapped("qty_delivered"), [5.0, 5.0])

    def test_confirm_to_invoice_two_step_missing_stock(self):
        """Missing stock at the start of the route is still rejected, nothing is validated"""
        self.warehouse.delivery_steps = "pick_ship"
        product = self.env["product.product"].create({"name": "No stock", "type": "consu", "is_storable": True})
        order = self._create_order(product)
        with self.assertRaises(UserError):
            order.action_button_confirm_to_invoice()
        self.assertFalse(order.picking_ids.filtered(lambda p: p.state == "done"))
