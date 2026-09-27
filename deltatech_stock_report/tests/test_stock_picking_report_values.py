# © 2026 Deltatech / Terrabit
# See README.rst file on addons root folder for license details
# Values reported by stock.picking.report must keep the 19.0 convention:
# positive amount for receipts and deliveries, signed quantity by destination.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockPickingReportValues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Report product",
                "type": "consu",
                "is_storable": True,
                "standard_price": 10.0,
                "weight": 2.0,
            }
        )

    def _validate_picking(self, picking_type, location, location_dest, qty):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "location_id": location.id,
                            "location_dest_id": location_dest.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.quantity = qty
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        return picking

    def test_report_values(self):
        receipt = self._validate_picking(self.warehouse.in_type_id, self.supplier_location, self.stock_location, 5)
        delivery = self._validate_picking(self.warehouse.out_type_id, self.stock_location, self.customer_location, 2)
        self.env.flush_all()

        Report = self.env["stock.picking.report"]
        line_in = Report.search([("picking_id", "=", receipt.id)])
        line_out = Report.search([("picking_id", "=", delivery.id)])
        self.assertEqual(len(line_in), 1)
        self.assertEqual(len(line_out), 1)

        self.assertAlmostEqual(line_in.product_qty, 5.0)
        self.assertAlmostEqual(line_in.amount, 50.0)
        self.assertAlmostEqual(line_in.price, 10.0)
        self.assertAlmostEqual(line_in.product_weight, 10.0)
        self.assertEqual(line_in.product_uom, self.product.uom_id)
        self.assertEqual(line_in.picking_type_code, "incoming")

        # outgoing: quantity negative (destination not internal), amount positive as in 19.0
        self.assertAlmostEqual(line_out.product_qty, -2.0)
        self.assertAlmostEqual(line_out.amount, 20.0)
        self.assertAlmostEqual(line_out.price, 10.0)
        self.assertEqual(line_out.picking_type_code, "outgoing")

        groups = dict(
            (picking_type_id, (qty, amount))
            for picking_type_id, qty, amount in Report.read_group(
                [("product_id", "=", self.product.id)], ["picking_type_id"], ["product_qty:sum", "amount:sum"]
            )
        )
        self.assertEqual(groups[self.warehouse.in_type_id.id], (5.0, 50.0))
        self.assertEqual(groups[self.warehouse.out_type_id.id], (-2.0, 20.0))
