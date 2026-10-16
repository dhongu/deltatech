# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestReservedPickings(TransactionCase):
    """Butonul "Reserved Transfers" de pe produs arata transferurile care au rezervat produsul."""

    def setUp(self):
        super().setUp()
        self.warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
        self.stock_location = self.warehouse.lot_stock_id
        self.customer_location = self.env.ref("stock.stock_location_customers")
        self.product = self.env["product.product"].create({"name": "Test reserved", "is_storable": True})
        self.template = self.product.product_tmpl_id
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 10)

    def _create_delivery(self, qty):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        return picking

    def test_reserved_picking_counted(self):
        picking = self._create_delivery(4)
        self.assertEqual(picking.state, "assigned")
        self.assertEqual(self.product.reserved_picking_count, 1)
        self.assertEqual(self.template.reserved_picking_count, 1)
        for record in (self.product, self.template):
            action = record.action_view_reserved_pickings()
            self.assertEqual(action["res_model"], "stock.picking")
            self.assertEqual(action["domain"], [("id", "in", picking.ids)])
            self.assertFalse(action["context"]["create"])

    def test_partially_available_picking_counted(self):
        picking = self._create_delivery(15)
        self.assertEqual(picking.move_ids.state, "partially_available")
        self.assertEqual(self.template.reserved_picking_count, 1)

    def test_done_or_cancelled_picking_not_counted(self):
        done = self._create_delivery(3)
        done.move_ids.picked = True
        done._action_done()
        self._create_delivery(2).action_cancel()
        self.assertEqual(done.state, "done")
        self.assertEqual(self.template.reserved_picking_count, 0)
        self.assertEqual(self.product.reserved_picking_count, 0)

    def test_unreserved_picking_not_counted(self):
        picking = self._create_delivery(4)
        picking.do_unreserve()
        self.assertEqual(self.template.reserved_picking_count, 0)

    def test_service_has_no_reserved_pickings(self):
        service = self.env["product.product"].create({"name": "Test service", "type": "service"})
        self.assertEqual(service.reserved_picking_count, 0)
        self.assertEqual(service.product_tmpl_id.reserved_picking_count, 0)
