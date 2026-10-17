# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBackorder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create({"name": "Test Split", "is_storable": True})
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.stock_location, 10)

    def _create_partial_picking(self):
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
                            "product_uom_qty": 10,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.quantity = 4
        return picking

    def _get_backorder(self, picking):
        return self.env["stock.picking"].search([("backorder_id", "=", picking.id)])

    def test_split_transfer(self):
        picking = self._create_partial_picking()
        picking.action_split_transfer()

        backorder = self._get_backorder(picking)
        self.assertEqual(len(backorder), 1)
        self.assertEqual(picking.move_ids.product_uom_qty, 4)
        self.assertEqual(backorder.move_ids.product_uom_qty, 6)
        self.assertFalse(backorder.postponed)

    def test_split_transfer_postponed(self):
        self.env["ir.config_parameter"].sudo().set_param("backorders.postponed", "True")
        picking = self._create_partial_picking()
        picking.action_split_transfer()

        backorder = self._get_backorder(picking)
        self.assertEqual(len(backorder), 1)
        self.assertTrue(backorder.postponed)
        self.assertFalse(picking.postponed)
