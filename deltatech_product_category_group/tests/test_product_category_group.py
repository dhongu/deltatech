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

    def _create_picking(self, picking_type=None, location_source=None, location_dest=None, company=None):
        picking_type = picking_type or self.env.ref("stock.picking_type_internal")
        location_source = location_source or self.location_source
        location_dest = location_dest or self.location_dest
        picking = (
            self.env["stock.picking"]
            .with_company(company or self.env.company)
            .create(
                {
                    "location_id": location_source.id,
                    "location_dest_id": location_dest.id,
                    "picking_type_id": picking_type.id,
                    "user_id": False,
                    "move_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "product_uom_qty": 10,
                                "product_uom": self.product.uom_id.id,
                                "location_id": location_source.id,
                                "location_dest_id": location_dest.id,
                            },
                        )
                    ],
                }
            )
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

    def test_only_eligible_users_are_candidates(self):
        group_stock_user = self.env.ref("stock.group_stock_user")
        no_stock_user = self.env["res.users"].create(
            {"name": "No Stock", "login": "no_stock", "group_ids": [(6, 0, [self.user_group.id])]}
        )
        portal_user = self.env["res.users"].create(
            {
                "name": "Portal Picker",
                "login": "portal_picker",
                "group_ids": [(6, 0, [self.user_group.id, self.env.ref("base.group_portal").id])],
            }
        )
        inactive_user = self.env["res.users"].create(
            {
                "name": "Inactive Picker",
                "login": "inactive_picker",
                "group_ids": [(6, 0, [self.user_group.id, group_stock_user.id])],
            }
        )
        inactive_user.active = False
        other_company = self.env["res.company"].create({"name": "Other Company"})
        other_company_user = self.env["res.users"].create(
            {
                "name": "Other Company Picker",
                "login": "other_company_picker",
                "company_id": other_company.id,
                "company_ids": [(6, 0, other_company.ids)],
                "group_ids": [(6, 0, [self.user_group.id, group_stock_user.id])],
            }
        )
        excluded = no_stock_user | portal_user | inactive_user | other_company_user
        assigned = self.env["res.users"]
        for _i in range(4):
            picking = self._create_picking()
            picking.responsible_determination()
            assigned |= picking.user_id
        self.assertEqual(assigned, self.user_1 | self.user_2)
        self.assertFalse(assigned & excluded)

    def test_no_eligible_user_leaves_picking_unassigned(self):
        self.user_1.group_ids = [(3, self.env.ref("stock.group_stock_user").id)]
        self.user_2.group_ids = [(3, self.env.ref("stock.group_stock_user").id)]
        picking = self._create_picking()
        picking.responsible_determination()
        self.assertFalse(picking.user_id)
        self.assertFalse(picking.user_group_id)

    def test_ready_count_is_per_company(self):
        company2 = self.env["res.company"].create({"name": "Second Company"})
        self.product.company_id = False
        self.user_1.write({"company_ids": [(4, company2.id)]})
        warehouse2 = self.env["stock.warehouse"].search([("company_id", "=", company2.id)], limit=1)
        picking_type2 = warehouse2.out_type_id
        source2 = warehouse2.lot_stock_id
        dest2 = self.env.ref("stock.stock_location_customers")
        self.env["stock.quant"]._update_available_quantity(self.product, source2, 100.0)
        # user_1 has many ready transfers in the second company only
        for _i in range(3):
            other = self._create_picking(picking_type2, source2, dest2, company2)
            self.assertEqual(other.state, "assigned")
            other.user_id = self.user_1
        # in the main company user_1 is still free: the transfers of the other company do not count
        picking = self._create_picking()
        picking.user_id = self.user_2
        first = self._create_picking()
        first.responsible_determination()
        self.assertEqual(first.user_id, self.user_1)

    def test_responsible_button_restricted_to_managers(self):
        view_id = self.env.ref("stock.vpicktree").id
        arch = self.env["stock.picking"].with_user(self.user_1).get_view(view_id, "list")["arch"]
        self.assertNotIn("responsible_determination", arch)
        self.user_1.group_ids = [(4, self.env.ref("stock.group_stock_manager").id)]
        arch = self.env["stock.picking"].with_user(self.user_1).get_view(view_id, "list")["arch"]
        self.assertIn("responsible_determination", arch)

    def test_category_from_unreserved_move(self):
        """In a partially reserved transfer the category of the unreserved move counts too"""
        group_stock_user = self.env.ref("stock.group_stock_user")
        group_b = self.env["res.groups"].create({"name": "Test Category Group B"})
        user_b = self.env["res.users"].create(
            {
                "name": "Test Picker B",
                "login": "test_picker_b",
                "group_ids": [(6, 0, [group_b.id, group_stock_user.id])],
            }
        )
        category_a = self.env["product.category"].create({"name": "No Group Category"})
        category_b = self.env["product.category"].create({"name": "Group B Category", "user_group_id": group_b.id})
        product_a = self.env["product.product"].create(
            {"name": "Reserved Product", "is_storable": True, "categ_id": category_a.id}
        )
        product_b = self.env["product.product"].create(
            {"name": "Unreserved Product", "is_storable": True, "categ_id": category_b.id}
        )
        self.env["stock.quant"]._update_available_quantity(product_a, self.location_source, 100.0)
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.location_source.id,
                "location_dest_id": self.location_dest.id,
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
                "move_type": "direct",
                "user_id": False,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 10,
                            "product_uom": product.uom_id.id,
                            "location_id": self.location_source.id,
                            "location_dest_id": self.location_dest.id,
                        },
                    )
                    for product in (product_a, product_b)
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.user_id = False
        self.assertEqual(picking.state, "assigned")
        self.assertEqual(picking.move_line_ids.product_id, product_a)
        picking.responsible_determination()
        self.assertEqual(picking.user_id, user_b)
        self.assertEqual(picking.user_group_id, group_b)
