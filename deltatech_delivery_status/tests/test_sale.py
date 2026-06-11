# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSale(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )

    def test_sale(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 10

        self.so = so.save()
        self.so.action_confirm()

        self.picking = self.so.picking_ids
        self.picking.action_assign()

        self.so.postpone_delivery()
        self.so.release_delivery()

    def _create_confirmed_order(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [(0, 0, {"product_id": self.product_a.id, "product_uom_qty": 10})],
            }
        )
        order.action_confirm()
        return order

    def test_postponed_delivery_recompute(self):
        order = self._create_confirmed_order()
        self.assertFalse(order.postponed_delivery)

        order.postpone_delivery()
        self.assertTrue(order.postponed_delivery)

        order.release_delivery()
        self.assertFalse(order.postponed_delivery)

    def test_release_delivery_on_payment_done(self):
        provider = self.env["payment.provider"].create(
            {
                "name": "Test Provider",
                "code": "none",
                "postponed_delivery": True,
            }
        )
        order = self._create_confirmed_order()
        order.postpone_delivery()
        self.assertTrue(order.postponed_delivery)

        tx = self.env["payment.transaction"].create(
            {
                "provider_id": provider.id,
                "payment_method_id": self.env.ref("payment.payment_method_unknown").id,
                "amount": order.amount_total,
                "currency_id": order.currency_id.id,
                "partner_id": self.partner_a.id,
                "sale_order_ids": [(6, 0, order.ids)],
            }
        )
        tx._set_done()
        self.assertFalse(order.postponed_delivery)
