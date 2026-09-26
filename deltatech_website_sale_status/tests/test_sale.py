# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from unittest.mock import patch

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

    def test_stage_without_sale_purchase(self):
        """The stage is computed even when sale_purchase is not installed.

        The confirmed order has no picking left, which is the branch that looks
        for purchase RFQs. The field is hidden from `_fields` to reproduce a
        database without sale_purchase.
        """
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a
        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 5
        so = so.save()
        so.action_confirm()
        so.picking_ids.action_cancel()
        so.picking_ids.unlink()

        fields_without_purchase = {
            name: field for name, field in type(so)._fields.items() if name != "purchase_order_count"
        }
        with patch.object(type(so), "_fields", fields_without_purchase):
            so._compute_stage()
        self.assertEqual(so.stage, "waiting")
