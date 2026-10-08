from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestManualBackorder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({"name": "Split Product", "is_storable": True})
        warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": warehouse.out_type_id.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 5.0,
                            "location_id": warehouse.lot_stock_id.id,
                            "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                        },
                    )
                ],
            }
        )
        cls.picking.action_confirm()
        cls.move = cls.picking.move_ids

    def _wizard(self, kept_qty):
        wizard = self.env["stock.picking.manual.backorder"].with_context(active_id=self.picking.id).create({})
        wizard.line_ids.kept_qty = kept_qty
        return wizard

    def _backorders(self):
        return self.env["stock.picking"].search([("backorder_id", "=", self.picking.id)])

    def test_split_keeps_quantity(self):
        self._wizard(3.0).do_create_backorder()
        self.assertEqual(self.move.product_uom_qty, 3.0)
        self.assertEqual(self._backorders().move_ids.product_uom_qty, 2.0)

    def test_kept_above_demand_refused(self):
        """PICKSPLIT-002: an excessive kept quantity no longer inflates the demand"""
        wizard = self._wizard(7.0)
        with self.assertRaises(UserError):
            wizard.do_create_backorder()
        self.assertEqual(self.move.product_uom_qty, 5.0)
        self.assertFalse(self._backorders())

    def test_negative_kept_refused(self):
        wizard = self._wizard(-1.0)
        with self.assertRaises(UserError):
            wizard.do_create_backorder()
        self.assertEqual(self.move.product_uom_qty, 5.0)
        self.assertFalse(self._backorders())

    def test_stale_wizard_uses_current_demand(self):
        """The demand shown in the wizard may be outdated; the split follows the move"""
        wizard = self._wizard(4.0)
        self.move.product_uom_qty = 3.0
        with self.assertRaises(UserError):
            wizard.do_create_backorder()
        self.assertEqual(self.move.product_uom_qty, 3.0)
        self.assertFalse(self._backorders())
