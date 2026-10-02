# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.company.id)], limit=1)
        cls.warehouse_other = cls.env["stock.warehouse"].create(
            {"name": "Second Warehouse", "code": "WH2T", "company_id": cls.company.id}
        )
        # depozitul secundar trebuie sa fie primul gasit de prepare_transfer
        others = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id), ("id", "not in", (cls.warehouse | cls.warehouse_other).ids)]
        )
        others.write({"sequence": 100})
        cls.warehouse_other.sequence = 1

        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "Storable Product", "type": "consu", "is_storable": True}
        )
        cls.service = cls.env["product.product"].create({"name": "Service", "type": "service"})

    def _create_order(self, qty, product=None):
        product = product or self.product
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "order_line": [(0, 0, {"product_id": product.id, "product_uom_qty": qty})],
            }
        )

    def _put_stock(self, warehouse, qty):
        self.env["stock.quant"]._update_available_quantity(self.product, warehouse.lot_stock_id, qty)

    def _transfers(self, order):
        return self.env["stock.picking"].search(
            [("origin", "=", order.name), ("picking_type_id", "=", self.warehouse_other.int_type_id.id)]
        )

    def test_transfer_generated_from_other_warehouse(self):
        self._put_stock(self.warehouse_other, 3)
        order = self._create_order(5)
        order.action_confirm()

        transfer = self._transfers(order)
        self.assertEqual(len(transfer), 1)
        self.assertEqual(transfer.location_id, self.warehouse_other.lot_stock_id)
        self.assertEqual(transfer.location_dest_id, self.warehouse.lot_stock_id)
        self.assertEqual(transfer.partner_id, self.partner)
        self.assertEqual(transfer.move_ids.product_id, self.product)
        # se transfera doar cat exista in depozitul secundar
        self.assertEqual(transfer.move_ids.product_uom_qty, 3)
        self.assertEqual(transfer.move_ids.uom_id, self.product.uom_id)
        self.assertEqual(transfer.state, "assigned")
        self.assertIn(transfer.name, order.message_ids.mapped("body")[0])

    def test_transfer_limited_to_demand(self):
        self._put_stock(self.warehouse_other, 10)
        self._put_stock(self.warehouse, 2)
        order = self._create_order(5)
        order.action_confirm()

        transfer = self._transfers(order)
        self.assertEqual(transfer.move_ids.product_uom_qty, 3)

    def test_no_transfer_when_stock_available(self):
        self._put_stock(self.warehouse_other, 10)
        self._put_stock(self.warehouse, 10)
        order = self._create_order(5)
        order.action_confirm()
        self.assertFalse(self._transfers(order))

    def test_no_transfer_without_stock_or_for_service(self):
        order = self._create_order(5)
        order.action_confirm()
        self.assertFalse(self._transfers(order))

        self._put_stock(self.warehouse_other, 10)
        order_service = self._create_order(5, product=self.service)
        order_service.action_confirm()
        self.assertFalse(self._transfers(order_service))

    def test_auto_confirm_transfer(self):
        self._put_stock(self.warehouse_other, 5)
        order = self._create_order(5)
        order.with_context(confirm_transfer=True).action_confirm()

        transfer = self._transfers(order)
        self.assertEqual(transfer.state, "done")
        self.assertEqual(transfer.move_ids.quantity, 5)
        self.assertEqual(self.product.with_context(warehouse_id=self.warehouse.id).qty_available, 5)
        self.assertEqual(self.product.with_context(warehouse_id=self.warehouse_other.id).qty_available, 0)

    def test_group_transfer_with_delivery(self):
        self.warehouse.group_transfer_with_delivery = True
        self._put_stock(self.warehouse_other, 5)
        order = self._create_order(5)
        order.action_confirm()

        transfer = self._transfers(order)
        self.assertTrue(order.stock_reference_ids)
        self.assertEqual(transfer.move_ids.reference_ids, order.stock_reference_ids)
