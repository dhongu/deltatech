from odoo.exceptions import UserError, ValidationError
from odoo.tests import common


class TestStageRoute(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.phase_a = cls.env["sale.order.phase"].create({"name": "Phase A"})
        cls.phase_b = cls.env["sale.order.phase"].create({"name": "Phase B"})
        cls.phase_c = cls.env["sale.order.phase"].create({"name": "Phase C"})

        cls.route = cls.env["sale.order.stage.route"].create(
            {
                "name": "Route 1",
                "line_ids": [
                    (0, 0, {"sequence": 1, "phase_id": cls.phase_a.id}),
                    (0, 0, {"sequence": 2, "phase_id": cls.phase_b.id}),
                    (0, 0, {"sequence": 3, "phase_id": cls.phase_c.id}),
                ],
            }
        )

        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    def test_01_route_constraints(self):
        # Unique stages
        with self.assertRaises(ValidationError):
            self.env["sale.order.stage.route"].create(
                {
                    "name": "Invalid Route",
                    "line_ids": [
                        (0, 0, {"sequence": 1, "phase_id": self.phase_a.id}),
                        (0, 0, {"sequence": 2, "phase_id": self.phase_a.id}),
                    ],
                }
            )

        # At least two stages
        with self.assertRaises(ValidationError):
            self.env["sale.order.stage.route"].create(
                {
                    "name": "Short Route",
                    "line_ids": [(0, 0, {"sequence": 1, "phase_id": self.phase_a.id})],
                }
            )

    def test_02_route_initial_stage(self):
        # Case 1: Create Sale Order with a route - should set the first stage of the route
        sale_order = self.env["sale.order"].create({"partner_id": self.partner.id, "stage_route_id": self.route.id})
        self.assertEqual(sale_order.phase_id, self.phase_a, "Initial phase should be the first stage of the route")

        # Case 2: Change route on an existing Sale Order - should update to the first stage of the new route
        route_2 = self.env["sale.order.stage.route"].create(
            {
                "name": "Route 2",
                "line_ids": [
                    (0, 0, {"sequence": 1, "phase_id": self.phase_b.id}),
                    (0, 0, {"sequence": 2, "phase_id": self.phase_c.id}),
                ],
            }
        )
        sale_order.write({"stage_route_id": route_2.id})
        self.assertEqual(sale_order.phase_id, self.phase_b, "Phase should update to the first stage of the new route")

        # Case 3: Create Sale Order with both route and explicit phase - explicit phase should win
        sale_order_custom = self.env["sale.order"].create(
            {"partner_id": self.partner.id, "stage_route_id": self.route.id, "phase_id": self.phase_b.id}
        )
        self.assertEqual(
            sale_order_custom.phase_id, self.phase_b, "Explicit phase should override the route's first stage"
        )

        # Case 4: Update Sale Order with both route and explicit phase - explicit phase should win
        sale_order.write({"stage_route_id": self.route.id, "phase_id": self.phase_c.id})
        self.assertEqual(
            sale_order.phase_id, self.phase_c, "Explicit phase in write should override the route's first stage"
        )

    def test_03_picking_transition(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "stage_route_id": self.route.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_4").id,
                            "product_uom_qty": 10,
                        },
                    )
                ],
            }
        )
        sale_order.action_confirm()

        picking = sale_order.picking_ids[0]
        # Initially, phase might be set by action_confirm (e.g. 'confirmed' from base module)
        # We set it to first phase of route
        sale_order.phase_id = self.phase_a

        # Validate picking -> should move to Phase B
        picking.button_validate()
        self.assertEqual(sale_order.phase_id, self.phase_b)
        self.assertNotEqual(picking.state, "done")

        # Validate picking again (second phase) -> should move to Phase C (last phase) AND validate
        # Need to set quantities to validate without wizard
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        res = picking.button_validate()
        self.assertEqual(sale_order.phase_id, self.phase_c)
        self.assertEqual(picking.state, "done")
        self.assertEqual(res, True)

    def test_04_picking_not_in_route_error(self):
        phase_x = self.env["sale.order.phase"].create({"name": "Phase X"})
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "stage_route_id": self.route.id,
                "phase_id": phase_x.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_4").id,
                            "product_uom_qty": 10,
                        },
                    )
                ],
            }
        )
        sale_order.action_confirm()
        # phase_id might have changed in action_confirm, force it back to phase_x
        sale_order.phase_id = phase_x

        picking = sale_order.picking_ids[0]
        with self.assertRaises(UserError):
            picking.button_validate()

    def test_06_picking_phase_admin_restriction(self):
        # Create a user without phase admin group, but with stock and sale groups to avoid base ACL errors
        user_test = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("stock.group_stock_user").id,
                            self.env.ref("sales_team.group_sale_salesman_all_leads").id,
                        ],
                    )
                ],
            }
        )

        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "stage_route_id": self.route.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_4").id,
                            "product_uom_qty": 10,
                        },
                    )
                ],
            }
        )
        sale_order.action_confirm()
        sale_order.phase_id = self.phase_a
        picking = sale_order.picking_ids[0]

        # Test user cannot move to Phase C (skipping Phase B)
        with self.assertRaises(ValidationError):
            picking.with_user(user_test).write({"phase_id": self.phase_c.id})

        # Test user can move to Phase B (next phase)
        picking.with_user(user_test).write({"phase_id": self.phase_b.id})
        self.assertEqual(sale_order.phase_id, self.phase_b)

        # Create a user with phase admin group
        user_admin = self.env["res.users"].create(
            {
                "name": "Admin User",
                "login": "admin_user",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("stock.group_stock_user").id,
                            self.env.ref("sales_team.group_sale_salesman_all_leads").id,
                            self.env.ref("deltatech_sale_stage_route.group_phase_admin").id,
                        ],
                    )
                ],
            }
        )

        # Admin user can move back to Phase A
        picking.with_user(user_admin).write({"phase_id": self.phase_a.id})
        self.assertEqual(sale_order.phase_id, self.phase_a)
