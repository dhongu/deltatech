from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPickingRestrictPolicy(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Restricted Delivery",
                "code": "outgoing",
                "sequence_code": "RDEL",
                "restrict_quantities": True,
                "restrict_new_products": True,
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Restricted Product", "type": "consu"})
        cls.extra_product = cls.env["product.product"].create({"name": "Extra Product", "type": "consu"})

    def _create_picking(self, qty, uom):
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.picking_type.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "product_uom": uom.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.quantity = qty
        return picking

    def test_validate_other_uom_matching_demand(self):
        # 1 dozen ordered, 1 dozen done: must validate (12 units == 1 dozen)
        picking = self._create_picking(1, self.uom_dozen)
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    def test_validate_quantity_lower_than_demand(self):
        picking = self._create_picking(10, self.uom_unit)
        picking.move_ids.quantity = 7
        picking.move_ids.picked = True
        with self.assertRaisesRegex(Exception, "Done quantities not equal to reserved"):
            picking.button_validate()

    def test_validate_extra_product_line(self):
        picking = self._create_picking(10, self.uom_unit)
        self.env["stock.move.line"].create(
            {
                "picking_id": picking.id,
                "product_id": self.extra_product.id,
                "product_uom_id": self.uom_unit.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "quantity": 5,
            }
        )
        picking.move_ids.picked = True
        with self.assertRaisesRegex(Exception, "Unrecognized product"):
            picking.button_validate()

    def test_validate_additional_move(self):
        picking = self._create_picking(10, self.uom_unit)
        self.env["stock.move"].with_context(default_picking_id=picking.id).create(
            {
                "product_id": self.extra_product.id,
                "product_uom_qty": 5,
                "product_uom": self.uom_unit.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_id": picking.id,
                "quantity": 5,
            }
        )
        picking.move_ids.picked = True
        with self.assertRaisesRegex(Exception, "Unrecognized product"):
            picking.button_validate()

    def test_validate_matching_demand(self):
        picking = self._create_picking(10, self.uom_unit)
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")
