# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReplenishmentExplanationLogic(TransactionCase):
    """Cover the live reconstruction of the orderpoint computation
    (_get_replenishment_explanation), the risk findings, the scheduled-move
    breakdown and the wizard / actions that render it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].create({"name": "WH Replenishment Explain", "code": "WRX"})
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env["stock.location"].create(
            {"name": "RX Supplier", "usage": "supplier", "location_id": False}
        )
        cls.customer_location = cls.env["stock.location"].create(
            {"name": "RX Customer", "usage": "customer", "location_id": False}
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_pack = cls.env["uom.uom"].create(
            {"name": "RX Pack of 12", "relative_factor": 12.0, "relative_uom_id": cls.uom_unit.id}
        )
        # Own supply route: a pull rule supplier -> WH stock, so rule_ids resolve
        # without depending on purchase / mrp being installed.
        cls.route = cls.env["stock.route"].create(
            {
                "name": "RX Supply Route",
                "product_selectable": True,
                "rule_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "RX Supplier -> Stock",
                            "action": "pull",
                            "procure_method": "make_to_stock",
                            "location_src_id": cls.supplier_location.id,
                            "location_dest_id": cls.stock_location.id,
                            "picking_type_id": cls.warehouse.in_type_id.id,
                            "warehouse_id": cls.warehouse.id,
                        },
                    )
                ],
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "RX Product",
                "type": "consu",
                "is_storable": True,
                "uom_id": cls.uom_unit.id,
                "route_ids": [(6, 0, cls.route.ids)],
            }
        )

    # ------------------------------------------------------------------ helpers
    def _orderpoint(self, **vals):
        values = {
            "product_id": self.product.id,
            "location_id": self.stock_location.id,
            "warehouse_id": self.warehouse.id,
            "product_min_qty": 5.0,
            "product_max_qty": 10.0,
            "trigger": "manual",
        }
        values.update(vals)
        return self.env["stock.warehouse.orderpoint"].create(values)

    def _move(self, src, dest, qty, date):
        move = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": qty,
                "location_id": src.id,
                "location_dest_id": dest.id,
                "date": date,
            }
        )
        move._action_confirm()
        return move

    def _risk_kw(self, **kw):
        base = {
            "below_min": False,
            "forecast": 10.0,
            "min_qty": 5.0,
            "max_qty": 10.0,
            "rounded_to_order": 0.0,
            "raw_to_order": 0.0,
            "no_vendor_delay": 0.0,
            "horizon_days": 0,
            "beyond_qty": 0.0,
            "beyond_date": False,
            "lead_horizon_date": fields.Date.today(),
            "multiple_name": "",
            "rounding": 0.01,
        }
        base.update(kw)
        return base

    @staticmethod
    def _titles(risks):
        return [risk["title"] for risk in risks]

    # ------------------------------------------------------------ explanation
    def test_explanation_below_min_values(self):
        orderpoint = self._orderpoint()
        values = orderpoint._get_replenishment_explanation()

        self.assertEqual(values["orderpoint"], orderpoint)
        self.assertEqual(values["product_name"], self.product.display_name)
        self.assertEqual(values["location_name"], self.stock_location.display_name)
        self.assertEqual(values["warehouse_name"], self.warehouse.display_name)
        self.assertEqual(values["uom_name"], self.product.uom_id.name)
        self.assertEqual(values["trigger"], "manual")
        self.assertTrue(values["has_rules"])
        self.assertIn("RX Supplier -> Stock", values["rule_names"])
        self.assertTrue(values["below_min"])
        self.assertFalse(values["is_manual_override"])
        self.assertTrue(values["in_progress_zero"])
        self.assertEqual(values["multiple_name"], "")
        fmt = orderpoint._explain_fmt
        self.assertEqual(values["on_hand"], fmt(0.0))
        self.assertEqual(values["forecast"], fmt(0.0))
        self.assertEqual(values["min_qty"], fmt(5.0))
        self.assertEqual(values["max_qty"], fmt(10.0))
        self.assertEqual(values["target"], fmt(10.0))
        self.assertEqual(values["raw_to_order"], fmt(10.0))
        self.assertEqual(values["rounded_to_order"], fmt(10.0))
        self.assertEqual(values["qty_to_order"], fmt(10.0))
        self.assertTrue(values["lead_horizon_date"])
        self.assertTrue(values["today"])
        # On hand (0) < Min (5) -> Odoo sets the deadline to today.
        self.assertTrue(values["deadline_date"])
        self.assertFalse(values["horizon_from_context"])
        self.assertEqual(values["horizon_days"], int(orderpoint.get_horizon_days()))
        self.assertIsInstance(values["delay_rows"], list)
        for row in values["delay_rows"]:
            self.assertIsInstance(row[1], str)
        # Diagram is computed from the same numbers: a 'to order' gap is drawn.
        self.assertTrue(values["diagram"]["below_min"])
        self.assertGreater(values["diagram"]["to_order_w"], 0.0)
        # Supply route available, nothing beyond the horizon -> "all clear".
        self.assertEqual(self._titles(values["risks"]), ["No visibility or horizon issues detected"])
        self.assertEqual(values["risks"][0]["level"], "success")

    def test_explanation_scheduled_moves_and_beyond_horizon(self):
        orderpoint = self._orderpoint(product_min_qty=0.0, product_max_qty=0.0)
        now = fields.Datetime.now()
        self._move(self.supplier_location, self.stock_location, 7.0, now)
        self._move(self.stock_location, self.customer_location, 3.0, now)
        far = now + timedelta(days=400)
        self._move(self.stock_location, self.customer_location, 4.0, far)
        self._move(self.stock_location, self.customer_location, 2.0, far + timedelta(days=5))

        values = orderpoint._get_replenishment_explanation()
        fmt = orderpoint._explain_fmt
        self.assertEqual(values["incoming"], fmt(7.0))
        self.assertEqual(values["outgoing"], fmt(3.0))
        self.assertEqual(values["virtual_at_horizon"], fmt(4.0))
        self.assertFalse(values["below_min"])
        self.assertEqual(values["raw_to_order"], fmt(0.0))
        self.assertEqual(values["rounded_to_order"], fmt(0.0))

        beyond = [r for r in values["risks"] if r["title"] == "Demand beyond the horizon is invisible"]
        self.assertEqual(len(beyond), 1)
        self.assertEqual(beyond[0]["level"], "warning")
        self.assertIn(fmt(6.0), beyond[0]["detail"])

    def test_scheduled_moves_direct(self):
        orderpoint = self._orderpoint()
        now = fields.Datetime.now()
        self._move(self.supplier_location, self.stock_location, 5.0, now)
        self._move(self.stock_location, self.customer_location, 1.0, now)
        late = self._move(self.stock_location, self.customer_location, 2.0, now + timedelta(days=30))
        later = self._move(self.stock_location, self.customer_location, 3.0, now + timedelta(days=60))
        # A cancelled move is not an open flow and must be ignored.
        cancelled = self._move(self.stock_location, self.customer_location, 50.0, now)
        cancelled._action_cancel()

        incoming, outgoing, beyond_qty, beyond_date = orderpoint._explain_scheduled_moves(now + timedelta(days=1))
        self.assertEqual(incoming, 5.0)
        self.assertEqual(outgoing, 1.0)
        self.assertEqual(beyond_qty, 5.0)
        self.assertEqual(beyond_date, late.date)
        self.assertLess(late.date, later.date)

        incoming, outgoing, beyond_qty, beyond_date = orderpoint._explain_scheduled_moves(now + timedelta(days=90))
        self.assertEqual(outgoing, 6.0)
        self.assertEqual(beyond_qty, 0.0)
        self.assertFalse(beyond_date)

    def test_explanation_potential_stockout_despite_no_order(self):
        # On hand 0 < Min 5 -> deadline today; a receipt inside the horizon lifts the
        # forecast above Min, so nothing is ordered although a stockout is flagged.
        orderpoint = self._orderpoint()
        self._move(self.supplier_location, self.stock_location, 20.0, fields.Datetime.now())
        values = orderpoint._get_replenishment_explanation()
        self.assertFalse(values["below_min"])
        self.assertTrue(values["deadline_date"])
        self.assertIn("Potential stockout despite no order", self._titles(values["risks"]))

    def test_explanation_native_replenishment_multiple(self):
        self.product.uom_ids = [(6, 0, self.uom_pack.ids)]
        orderpoint = self._orderpoint(replenishment_uom_id=self.uom_pack.id)
        values = orderpoint._get_replenishment_explanation()
        fmt = orderpoint._explain_fmt
        self.assertEqual(values["multiple_name"], self.uom_pack.display_name)
        self.assertEqual(values["raw_to_order"], fmt(10.0))
        self.assertEqual(values["rounded_to_order"], fmt(12.0))
        rounded = [r for r in values["risks"] if r["title"] == "Rounded up to a multiple"]
        self.assertEqual(len(rounded), 1)
        self.assertEqual(rounded[0]["level"], "info")
        self.assertIn(self.uom_pack.display_name, rounded[0]["detail"])

    def test_explanation_manual_override_and_snooze(self):
        orderpoint = self._orderpoint()
        orderpoint.qty_to_order_manual = 33.0
        orderpoint.snoozed_until = fields.Date.today() + timedelta(days=3)
        values = orderpoint._get_replenishment_explanation()
        self.assertTrue(values["is_manual_override"])
        self.assertEqual(values["qty_to_order"], orderpoint._explain_fmt(33.0))
        titles = self._titles(values["risks"])
        self.assertIn("Manual quantity override", titles)
        self.assertIn("Snoozed", titles)
        self.assertNotIn("No visibility or horizon issues detected", titles)

    def test_explanation_legacy_multiple_label(self):
        # Without deltatech_stock_orderpoint_multiple, `qty_multiple` is read via getattr;
        # simulate the legacy value to check how the multiple is labelled.
        orderpoint = self._orderpoint()
        if "qty_multiple" in orderpoint._fields:
            self.skipTest("covered by test_legacy_qty_multiple with the real field")
        with patch.object(type(orderpoint), "qty_multiple", 6.0, create=True):
            values = orderpoint._get_replenishment_explanation()
        self.assertEqual(values["multiple_name"], f"{orderpoint._explain_fmt(6.0)} {orderpoint.product_uom_name}")

    def test_explanation_horizon_from_context(self):
        orderpoint = self._orderpoint()
        values = orderpoint.with_context(global_horizon_days=17)._get_replenishment_explanation()
        self.assertTrue(values["horizon_from_context"])
        self.assertEqual(values["horizon_days"], 17)

    # ------------------------------------------------------------------ risks
    def test_risks_no_rule(self):
        orderpoint = self._orderpoint()
        no_rule_op = orderpoint.new({"product_id": self.product.id, "location_id": self.stock_location.id})
        no_rule_op.rule_ids = False
        risks = no_rule_op._get_replenishment_risks(**self._risk_kw())
        self.assertEqual(self._titles(risks), ["No supply route / rule"])
        self.assertEqual(risks[0]["level"], "danger")

    def test_risks_no_vendor_delay(self):
        orderpoint = self._orderpoint()
        risks = orderpoint._get_replenishment_risks(**self._risk_kw(below_min=True, no_vendor_delay=365.0))
        no_vendor = [r for r in risks if r["title"] == "No vendor found"]
        self.assertEqual(len(no_vendor), 1)
        self.assertEqual(no_vendor[0]["level"], "danger")
        self.assertIn("365", no_vendor[0]["detail"])

    def test_risks_beyond_horizon_without_date(self):
        orderpoint = self._orderpoint()
        risks = orderpoint._get_replenishment_risks(**self._risk_kw(below_min=True, beyond_qty=3.0, horizon_days=4))
        self.assertEqual(self._titles(risks), ["Demand beyond the horizon is invisible"])
        self.assertIn("4 days", risks[0]["detail"])

    def test_risks_multiple_without_inflation(self):
        orderpoint = self._orderpoint()
        risks = orderpoint._get_replenishment_risks(
            **self._risk_kw(below_min=True, raw_to_order=12.0, rounded_to_order=12.0, multiple_name="Pack")
        )
        self.assertEqual(self._titles(risks), ["No visibility or horizon issues detected"])

    def test_risks_past_snooze_ignored(self):
        orderpoint = self._orderpoint()
        orderpoint.snoozed_until = fields.Date.today() - timedelta(days=1)
        risks = orderpoint._get_replenishment_risks(**self._risk_kw(below_min=True))
        self.assertNotIn("Snoozed", self._titles(risks))

    # --------------------------------------------------------- wizard/actions
    def test_action_explain_replenishment_opens_wizard(self):
        orderpoint = self._orderpoint()
        action = orderpoint.action_explain_replenishment()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "stock.replenishment.explanation")
        self.assertEqual(action["target"], "new")
        wizard = self.env["stock.replenishment.explanation"].browse(action["res_id"])
        self.assertEqual(wizard.orderpoint_id, orderpoint)
        self.assertEqual(wizard.product_id, self.product)
        self.assertEqual(wizard.warehouse_id, self.warehouse)
        self.assertEqual(wizard.qty_to_order, orderpoint.qty_to_order)
        self.assertEqual(wizard.qty_forecast, orderpoint.qty_forecast)
        html = str(wizard.explanation_html)
        self.assertIn("RX Product", html)
        self.assertIn("<svg", html)

    def test_wizard_without_orderpoint(self):
        wizard = self.env["stock.replenishment.explanation"].new({})
        self.assertFalse(wizard.explanation_html)

    def test_wizard_open_forecast_report(self):
        orderpoint = self._orderpoint()
        wizard = self.env["stock.replenishment.explanation"].create({"orderpoint_id": orderpoint.id})
        action = wizard.action_open_forecast_report()
        self.assertEqual(action["context"]["active_id"], self.product.id)
        self.assertEqual(action["context"]["active_model"], "product.product")

    def test_server_action(self):
        orderpoint = self._orderpoint()
        server_action = self.env.ref("deltatech_replenishment_explain.action_explain_replenishment_server")
        action = server_action.with_context(
            active_model="stock.warehouse.orderpoint", active_id=orderpoint.id, active_ids=orderpoint.ids
        ).run()
        self.assertEqual(action["res_model"], "stock.replenishment.explanation")
        wizard = self.env["stock.replenishment.explanation"].browse(action["res_id"])
        self.assertEqual(wizard.orderpoint_id, orderpoint)
