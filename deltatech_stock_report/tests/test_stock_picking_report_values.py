# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockPickingReportValues(TransactionCase):
    """Quantities, weights, prices and amounts of the Picking Analysis report"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Report Value Product",
                "type": "consu",
                "is_storable": True,
                "standard_price": 10.0,
                "weight": 2.0,
            }
        )

    def _create_picking(self, picking_type, location, location_dest, qty, uom=None):
        move_vals = {
            "product_id": self.product.id,
            "product_uom_qty": qty,
            "location_id": location.id,
            "location_dest_id": location_dest.id,
        }
        if uom:
            move_vals["product_uom"] = uom.id
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
                "move_ids": [(0, 0, move_vals)],
            }
        )
        picking.action_confirm()
        return picking

    def _validate(self, picking, qty):
        picking.move_ids.write({"quantity": qty, "picked": True})
        picking.with_context(cancel_backorder=True)._action_done()
        self.assertEqual(picking.state, "done")

    def _report_rows(self, pickings):
        self.env.flush_all()
        return self.env["stock.picking.report"].search([("picking_id", "in", pickings.ids)])

    def test_partial_done_uses_processed_quantity(self):
        """STOCKREPORT-001: demand 10, processed 4, no backorder"""
        picking = self._create_picking(self.warehouse.in_type_id, self.supplier_location, self.stock_location, 10.0)
        self._validate(picking, 4.0)
        self.assertEqual(picking.move_ids.product_uom_qty, 10.0)
        row = self._report_rows(picking)
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.product_qty, 4.0)
        self.assertAlmostEqual(row.product_weight, 8.0)
        self.assertAlmostEqual(row.amount, 40.0)
        self.assertAlmostEqual(row.price, 10.0)

    def test_quantity_in_product_uom(self):
        """STOCKREPORT-001: processed quantity converted into the product unit"""
        dozen = self.env.ref("uom.product_uom_dozen")
        picking = self._create_picking(
            self.warehouse.in_type_id, self.supplier_location, self.stock_location, 2.0, uom=dozen
        )
        self._validate(picking, 1.0)
        row = self._report_rows(picking)
        self.assertAlmostEqual(row.product_qty, 12.0)
        self.assertAlmostEqual(row.product_weight, 24.0)
        self.assertAlmostEqual(row.price, 10.0)

    def test_outgoing_amount_follows_quantity_sign(self):
        """STOCKREPORT-002: equal receipt and delivery cancel out in quantity and amount"""
        receipt = self._create_picking(self.warehouse.in_type_id, self.supplier_location, self.stock_location, 5.0)
        self._validate(receipt, 5.0)
        delivery = self._create_picking(self.warehouse.out_type_id, self.stock_location, self.customer_location, 5.0)
        self._validate(delivery, 5.0)
        in_row = self._report_rows(receipt)
        out_row = self._report_rows(delivery)
        self.assertAlmostEqual(in_row.product_qty, 5.0)
        self.assertAlmostEqual(in_row.amount, 50.0)
        self.assertAlmostEqual(out_row.product_qty, -5.0)
        self.assertAlmostEqual(out_row.amount, -50.0)
        self.assertAlmostEqual(out_row.price, 10.0)
        rows = in_row | out_row
        self.assertAlmostEqual(sum(rows.mapped("product_qty")), 0.0)
        self.assertAlmostEqual(sum(rows.mapped("amount")), 0.0)

    def test_zero_quantity_line_does_not_divide_by_zero(self):
        """STOCKREPORT-004: a zero-quantity done line must not break the report"""
        picking = self._create_picking(self.warehouse.in_type_id, self.supplier_location, self.stock_location, 3.0)
        self._validate(picking, 3.0)
        other = self.env["product.product"].create(
            {"name": "Report Zero Product", "type": "consu", "is_storable": True, "standard_price": 7.0}
        )
        self.env["stock.move"].create(
            {
                "picking_id": picking.id,
                "product_id": other.id,
                "product_uom_qty": 0.0,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
            }
        )
        zero_move = picking.move_ids.filtered(lambda m: m.product_id == other)
        self.assertEqual(zero_move.state, "done")
        # the column stays NULL on create; once valuation stores 0 the old SQL divided by zero
        zero_move.write({"value": 0.0})
        rows = self._report_rows(picking)
        rows.read(["product_qty", "price", "amount"])
        zero_row = rows.filtered(lambda r: r.product_id == other)
        self.assertAlmostEqual(zero_row.product_qty, 0.0)
        self.assertAlmostEqual(zero_row.amount, 0.0)
