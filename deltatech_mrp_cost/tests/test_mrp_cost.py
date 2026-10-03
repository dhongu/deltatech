# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import Form, tagged

from odoo.addons.mrp.tests.common import TestMrpCommon


@tagged("post_install", "-at_install")
class TestMrpOrder(TestMrpCommon):
    # the costs are configured on the BoM by a manufacturing manager
    _test_user_groups = ("mrp.group_mrp_manager", "stock.group_stock_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.group_user").write({"implied_ids": [(4, cls.env.ref("stock.group_production_lot").id)]})
        unrestricted_group = cls.env.ref("deltatech_restricted_access", raise_if_not_found=False)
        if unrestricted_group:
            cls.env.ref("base.group_user").write({"implied_ids": [(4, unrestricted_group.id)]})

    def test_basic(self):
        """Checks a basic manufacturing order: no routing (thus no workorders), no lot and
        consume strictly what's needed."""

        self.bom_1.write(
            {
                "overhead_amount": 100.0,
                "duration": 2.0,
                "utility_consumption": 10.0,
                "net_salary_rate": 20.0,
                "salary_contributions": 5.0,
            }
        )
        self.assertEqual(self.bom_1.duration, 2.0)

        self.product_1.sudo().is_storable = True  # setup master-data
        self.product_2.sudo().is_storable = True
        self.env["stock.quant"].create(
            {
                "location_id": self.stock_location.id,
                "product_id": self.product_1.id,
                "inventory_quantity": 500,
            }
        ).action_apply_inventory()
        self.env["stock.quant"].create(
            {
                "location_id": self.stock_location.id,
                "product_id": self.product_2.id,
                "inventory_quantity": 500,
            }
        ).action_apply_inventory()

        test_date_planned = fields.Datetime.now() - timedelta(days=1)
        test_quantity = 2.0  # bom_1 has product_qty = 4.0

        man_order = (
            self.env["mrp.production"]
            .with_user(self.user_mrp_user)
            .create(
                {
                    "product_id": self.product_4.id,
                    "bom_id": self.bom_1.id,
                    "uom_id": self.product_4.uom_id.id,
                    "product_qty": test_quantity,
                    "date_start": test_date_planned,
                    "location_src_id": self.stock_location.id,
                    "location_dest_id": self.output_location.id,
                }
            )
        )
        # self.env.cr.commit()
        # man_order.refresh()
        # print(f"DEBUG TEST: man_order={man_order.id}, duration={man_order.duration_cost}")

        # Check if values are copied from BoM and adjusted for quantity
        # duration = test_qty / bom_qty * bom_duration = 2.0 / 4.0 * 2.0 = 1.0
        self.assertEqual(man_order.overhead_amount, 100.0)
        self.assertEqual(man_order.duration_cost, 1.0)
        self.assertEqual(man_order.utility_consumption, 10.0)
        self.assertEqual(man_order.net_salary_rate, 20.0)
        self.assertEqual(man_order.salary_contributions, 5.0)

        man_order.action_confirm()

        # Check amount calculation before production
        # amount = materials + overhead + (utility + net_salary + contributions) * duration
        # materials = (product_1 price * 2) + (product_2 price * 1)  (since bom is for 4, and we make 2)
        # Note: TestMrpCommon setup product standard prices are usually 0 unless set.
        self.product_1.sudo().standard_price = 10.0
        self.product_2.sudo().standard_price = 20.0

        man_order._compute_amount()

        total_materials = 0.0
        for move in man_order.move_raw_ids:
            total_materials += move.product_id.standard_price * move.product_qty

        extra_costs = (
            man_order.overhead_amount
            + (man_order.utility_consumption + man_order.net_salary_rate + man_order.salary_contributions)
            * man_order.duration_cost
        )

        expected_amount = total_materials + extra_costs
        self.assertAlmostEqual(man_order.amount, expected_amount)
        self.assertAlmostEqual(man_order.calculate_price, expected_amount / 2.0)

    def test_cost_on_done_production(self):
        """Extra costs from the BoM are added to the finished move value (FIFO) and
        the production report renders the valuation columns."""
        self.bom_1.write(
            {
                "overhead_amount": 100.0,
                "duration": 2.0,
                "utility_consumption": 10.0,
                "net_salary_rate": 20.0,
                "salary_contributions": 5.0,
            }
        )
        category_fifo = (
            self.env["product.category"]
            .sudo()
            .create(  # setup master-data
                {"name": "Fifo MRP cost", "property_valuation": "periodic", "property_cost_method": "fifo"}
            )
        )
        (self.product_1 | self.product_2 | self.product_4).sudo().write(
            {"is_storable": True, "categ_id": category_fifo.id}
        )
        self.product_1.sudo().standard_price = 10.0
        self.product_2.sudo().standard_price = 20.0
        for product in self.product_1 | self.product_2:
            self.env["stock.quant"].create(
                {"location_id": self.stock_location.id, "product_id": product.id, "inventory_quantity": 500}
            ).action_apply_inventory()

        production = self.env["mrp.production"].create(
            {
                "product_id": self.product_4.id,
                "bom_id": self.bom_1.id,
                "uom_id": self.product_4.uom_id.id,
                "product_qty": 4.0,
            }
        )
        # duration = 4 / 4 * 2 = 2 hours
        self.assertEqual(production.duration_cost, 2.0)
        production.action_confirm()
        production.action_assign()
        mo_form = Form(production)
        mo_form.qty_producing = 4.0
        production = mo_form.save()
        production.move_raw_ids.picked = True
        production.button_mark_done()
        self.assertEqual(production.state, "done")

        # extra costs = 100 + (10 + 20 + 5) * 2 = 170 for 4 units
        self.assertAlmostEqual(production.extra_cost, 170.0 / 4.0)
        materials = sum(abs(move.value) for move in production.move_raw_ids)
        self.assertGreater(materials, 0.0)
        finished = production.move_finished_ids.filtered(lambda m: m.product_id == self.product_4)
        self.assertAlmostEqual(finished.value, materials + 170.0)
        self.assertAlmostEqual(production.amount, materials + 170.0)
        self.assertAlmostEqual(production.calculate_price, (materials + 170.0) / 4.0)

        # the barcode image does not matter here (and needs a reportlab renderPM backend)
        with patch.object(self.registry["ir.actions.report"], "barcode", lambda *args, **kwargs: b""):
            html = self.env["ir.actions.report"]._render_qweb_html(
                "mrp.action_report_production_order", production.ids
            )[0]
        self.assertIn(b"Finished Products", html)
        self.assertIn(b"Effective Quantity", html)
