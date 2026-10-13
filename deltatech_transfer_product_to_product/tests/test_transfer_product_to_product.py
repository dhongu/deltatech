from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestTransferProductToProduct(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.from_product = cls.env["product.product"].create({"name": "Replaced Product", "is_storable": True})
        cls.to_product = cls.env["product.product"].create({"name": "Replacement Product", "is_storable": True})
        cls.inventory_location = cls.from_product.property_stock_inventory
        cls.operation_type = cls.env["stock.picking.type"].create(
            {
                "name": "Product Replacement",
                "code": "internal",
                "sequence_code": "PTP",
                "warehouse_id": cls.warehouse.id,
                "create_backorder": "ask",
                "default_location_src_id": cls.stock_location.id,
                "default_location_dest_id": cls.stock_location.id,
            }
        )

    def _run_wizard(self, quantity):
        wizard = self.env["transfer.product.to.product"].create(
            {
                "from_product_id": self.from_product.id,
                "to_product_id": self.to_product.id,
                "quantity": quantity,
                "location_adjustment": self.stock_location.id,
                "location_id": self.inventory_location.id,
                "operation_type": self.operation_type.id,
            }
        )
        return wizard.action_confirm()

    def _legs(self):
        pickings = self.env["stock.picking"].search([("picking_type_id", "=", self.operation_type.id)], order="id")
        source = pickings.filtered(lambda p: p.product_id == self.from_product)
        target = pickings.filtered(lambda p: p.product_id == self.to_product)
        return source, target

    def _done_qty(self, pickings, product):
        moves = pickings.move_ids.filtered(lambda m: m.product_id == product and m.state == "done")
        return sum(moves.mapped("quantity"))

    def _qty(self, product):
        return product.with_context(location=self.stock_location.id).qty_available

    def test_fully_available(self):
        self.env["stock.quant"]._update_available_quantity(self.from_product, self.stock_location, 5)
        self._run_wizard(5)
        source, target = self._legs()
        self.assertEqual(source.state, "done")
        self.assertEqual(target.state, "done")
        self.assertEqual(self._qty(self.from_product), 0)
        self.assertEqual(self._qty(self.to_product), 5)

    def _partial_backorder_action(self):
        # PRODUCTTRANSFER-001: only 3 of 5 can be taken out of stock
        self.env["stock.quant"]._update_available_quantity(self.from_product, self.stock_location, 3)
        action = self._run_wizard(5)
        source, target = self._legs()
        # the replacement must not be completed alone while the source decision is pending
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("res_model"), "stock.backorder.confirmation")
        self.assertNotEqual(source[:1].state, "done")
        self.assertNotEqual(target[:1].state, "done")
        self.assertEqual(self._qty(self.to_product), 0)
        return action

    def test_partial_with_backorder(self):
        action = self._partial_backorder_action()
        Form(self.env["stock.backorder.confirmation"].with_context(**action["context"])).save().process()
        source, target = self._legs()
        self.assertEqual(self._done_qty(source, self.from_product), 3)
        self.assertEqual(self._done_qty(target, self.to_product), 3)
        self.assertEqual(self._qty(self.from_product), 0)
        self.assertEqual(self._qty(self.to_product), 3)
        # the remaining 2 stay pending on both legs, through native backorders
        self.assertEqual(len(source), 2)
        self.assertEqual(len(target), 2)
        self.assertEqual(source.backorder_ids.move_ids.product_uom_qty, 2)
        self.assertEqual(target.backorder_ids.move_ids.product_uom_qty, 2)
        self.assertNotEqual(target.backorder_ids.state, "done")

    def test_partial_without_backorder(self):
        action = self._partial_backorder_action()
        Form(
            self.env["stock.backorder.confirmation"].with_context(**action["context"])
        ).save().process_cancel_backorder()
        source, target = self._legs()
        self.assertEqual(len(source), 1)
        self.assertEqual(len(target), 1)
        self.assertEqual(source.state, "done")
        self.assertEqual(target.state, "done")
        self.assertEqual(self._done_qty(target, self.to_product), 3)
        self.assertEqual(self._qty(self.to_product), 3)

    def test_partial_never_backorder_policy(self):
        self.operation_type.create_backorder = "never"
        self.env["stock.quant"]._update_available_quantity(self.from_product, self.stock_location, 3)
        self._run_wizard(5)
        source, target = self._legs()
        self.assertEqual((source.state, target.state), ("done", "done"))
        self.assertEqual(self._done_qty(source, self.from_product), 3)
        self.assertEqual(self._done_qty(target, self.to_product), 3)
        self.assertFalse(source.backorder_ids | target.backorder_ids)
