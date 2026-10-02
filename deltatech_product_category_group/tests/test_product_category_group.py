from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockPicking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_stock_user = cls.env.ref("stock.group_stock_user")
        cls.user_group = cls.env["res.groups"].create({"name": "Test Category Group"})
        cls.user_1, cls.user_2 = cls.env["res.users"].create(
            [
                {
                    "name": f"Test Picker {i}",
                    "login": f"test_picker_{i}",
                    "group_ids": [(6, 0, [cls.user_group.id, group_stock_user.id])],
                }
                for i in (1, 2)
            ]
        )
        cls.parent_category = cls.env["product.category"].create(
            {"name": "Parent Category", "user_group_id": cls.user_group.id}
        )
        cls.product_category = cls.env["product.category"].create(
            {"name": "Child Category", "parent_id": cls.parent_category.id}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "categ_id": cls.product_category.id,
            }
        )
        cls.location_source = cls.env["stock.location"].create({"name": "Source Location", "usage": "internal"})
        cls.location_dest = cls.env["stock.location"].create({"name": "Destination Location", "usage": "internal"})
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.location_source, 100.0)

    def _create_picking(self):
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.location_source.id,
                "location_dest_id": self.location_dest.id,
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
                "user_id": False,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 10,
                            "uom_id": self.product.uom_id.id,
                            "location_id": self.location_source.id,
                            "location_dest_id": self.location_dest.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.user_id = False
        return picking

    def test_category_user_group_field(self):
        self.assertEqual(self.parent_category.user_group_id, self.user_group)
        self.assertFalse(self.product_category.user_group_id)

    def test_responsible_determination(self):
        picking = self._create_picking()
        self.assertEqual(picking.state, "assigned")
        picking.responsible_determination()
        # group taken from the parent category
        self.assertIn(picking.user_id, self.user_1 | self.user_2)
        self.assertEqual(picking.user_group_id, self.user_group)

    def test_responsible_balancing(self):
        first = self._create_picking()
        first.responsible_determination()
        second = self._create_picking()
        second.responsible_determination()
        # the second picking goes to the user without assigned pickings
        self.assertEqual(first.user_id | second.user_id, self.user_1 | self.user_2)

    def test_responsible_skipped(self):
        # picking with a responsible already set is not changed
        picking = self._create_picking()
        picking.user_id = self.env.user
        picking.responsible_determination()
        self.assertEqual(picking.user_id, self.env.user)
        self.assertFalse(picking.user_group_id)

        # picking not ready is not changed
        draft = self.env["stock.picking"].create(
            {
                "location_id": self.location_source.id,
                "location_dest_id": self.location_dest.id,
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
                "user_id": False,
            }
        )
        draft.responsible_determination()
        self.assertFalse(draft.user_id)
