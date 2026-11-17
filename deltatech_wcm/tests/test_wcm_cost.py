# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details

from datetime import datetime, timedelta

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWcmCost(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.CostLine = cls.env["wcm.cost.line"]
        cls.workcenter = cls.env["mrp.workcenter"].create(
            {
                "name": "WCM line",
                "costs_hour": 60.0,
                "employee_costs_hour": 0.0,
            }
        )
        cls.component = cls.env["product.product"].create(
            {
                "name": "WCM component",
                "type": "consu",
                "standard_price": 10.0,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "WCM finished product",
                "type": "consu",
            }
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product.product_tmpl_id.id,
                "product_qty": 1.0,
                "bom_line_ids": [Command.create({"product_id": cls.component.id, "product_qty": 2.0})],
                "operation_ids": [
                    Command.create(
                        {
                            "name": "Assembly",
                            "workcenter_id": cls.workcenter.id,
                            "time_mode": "manual",
                            "time_cycle_manual": 60.0,
                        }
                    )
                ],
            }
        )
        cls.production = cls.env["mrp.production"].create(
            {
                "product_id": cls.product.id,
                "bom_id": cls.bom.id,
                "product_qty": 5.0,
            }
        )
        cls.production.action_confirm()
        cls.production.qty_producing = 5.0
        cls.production._set_qty_producing()
        cls.production.move_raw_ids.picked = True
        cls.production.button_mark_done()
        cls.date_from = fields.Datetime.now() - timedelta(days=1)
        cls.date_to = fields.Datetime.now() + timedelta(hours=1)

    def _totals(self):
        data = self.CostLine._compute_cost_data(self.company, self.date_from, self.date_to)
        self.assertIn(self.product, data)
        return data[self.product]

    def _log_time(self, reason_xmlid, minutes):
        # Availability losses count only working hours of the work center calendar:
        # a Wednesday morning, inside the standard 40-hour calendar.
        start = datetime(2026, 11, 11, 9, 0)
        return self.env["mrp.workcenter.productivity"].create(
            {
                "workcenter_id": self.workcenter.id,
                "workorder_id": self.production.workorder_ids[:1].id,
                "loss_id": self.env.ref(reason_xmlid).id,
                "date_start": start,
                "date_end": start + timedelta(minutes=minutes),
            }
        )

    def test_actual_unit_cost_matches_mo_overview(self):
        """CA11: actual unit cost = unit cost of the MO Overview report."""
        self.assertEqual(self.production.state, "done")
        totals = self._totals()
        self.assertEqual(totals["good_qty"], 5.0)
        summary = self.env["report.mrp.report_mo_overview"]._get_report_data(self.production.id)["summary"]
        self.assertAlmostEqual(totals["actual_cost"] / totals["good_qty"], summary["mo_cost"] / summary["quantity"], 2)

    def test_standard_cost_and_deviation(self):
        """CA12: standard unit cost from the BoM; deviation per unit and in %."""
        totals = self._totals()
        bom_unit = self.env["report.mrp.report_bom_structure"]._get_bom_data(
            self.bom, self.production.warehouse_id, self.product, line_qty=1.0, ignore_stock=True
        )["bom_cost"]
        # 2 components x 10 + 1 hour x 60 per hour.
        self.assertAlmostEqual(bom_unit, 80.0, 2)
        self.assertAlmostEqual(totals["standard_cost"] / totals["good_qty"], bom_unit, 2)
        line = self.CostLine._refresh(self.company, self.date_from, self.date_to).filtered(
            lambda cost_line: cost_line.product_id == self.product
        )
        self.assertAlmostEqual(line.standard_unit_cost, 80.0, 2)
        self.assertAlmostEqual(line.deviation_unit, line.actual_unit_cost - line.standard_unit_cost, 2)
        self.assertAlmostEqual(
            line.deviation_pct, (line.actual_cost - line.standard_cost) * 100.0 / line.standard_cost, 2
        )

    def test_stoppage_and_changeover_cost(self):
        """CA13: stoppages and changeovers in lei per unit."""
        self._log_time("mrp.block_reason1", 30)  # equipment failure
        self._log_time("mrp.block_reason2", 15)  # setup and adjustments
        line = self.CostLine._refresh(self.company, self.date_from, self.date_to).filtered(
            lambda cost_line: cost_line.product_id == self.product
        )
        self.assertAlmostEqual(line.stoppage_cost, 30.0, 2)  # 0.5 h x 60
        self.assertAlmostEqual(line.changeover_cost, 15.0, 2)  # 0.25 h x 60
        self.assertAlmostEqual(line.stoppage_unit, 6.0, 2)
        self.assertAlmostEqual(line.changeover_unit, 3.0, 2)
        self.assertAlmostEqual(line.loss_unit, line.scrap_unit + 9.0 + line.energy_unit + line.waste_unit, 2)

    def test_cost_deviation_indicator(self):
        """CA14: Cost Deployment indicator with traffic light; no data without done orders."""
        seed = self.env.ref("deltatech_wcm.wcm_indicator_cost_deviation_unit")
        self.assertEqual(seed.pillar_id, self.env.ref("deltatech_wcm.wcm_pillar_cost_deployment"))
        self.assertEqual(seed.direction, "lower")
        pillar = self.env["wcm.pillar"].create({"name": "Cost test", "code": "cost_test"})
        indicator = self.env["wcm.indicator"].create(
            {
                "name": "Unit cost deviation",
                "pillar_id": pillar.id,
                "source": "cost_deviation",
                "target": 2,
                "warning": 5,
            }
        )
        totals = self._totals()
        expected = round((totals["actual_cost"] - totals["standard_cost"]) * 100.0 / totals["standard_cost"], 2)
        self.assertTrue(indicator.has_data)
        self.assertAlmostEqual(indicator.value, expected, 2)
        self.assertIn(indicator.state, ("green", "yellow", "red"))
        other_company = self.env["res.company"].create({"name": "WCM other company"})
        empty = self.env["wcm.indicator"].create(
            {
                "name": "Unit cost deviation, other company",
                "pillar_id": pillar.id,
                "company_id": other_company.id,
                "source": "cost_deviation",
                "target": 2,
                "warning": 5,
            }
        )
        self.assertFalse(empty.has_data)
        self.assertEqual(empty.state, "none")

    def test_manual_energy_cost_allocation(self):
        """CA15: a manual energy cost is spread over the good units and added to the actual cost."""
        actual_before = self._totals()["actual_cost"]
        today = fields.Date.context_today(self.production)
        self.env["wcm.cost.manual"].create(
            {
                "name": "Electricity",
                "workcenter_id": self.workcenter.id,
                "cost_type": "energy",
                "date_from": today,
                "date_to": today,
                "amount": 100.0,
            }
        )
        totals = self._totals()
        self.assertAlmostEqual(totals["energy_cost"], 100.0, 2)
        self.assertAlmostEqual(totals["actual_cost"], actual_before + 100.0, 2)
        line = self.CostLine._refresh(self.company, self.date_from, self.date_to).filtered(
            lambda cost_line: cost_line.product_id == self.product
        )
        self.assertAlmostEqual(line.energy_unit, 20.0, 2)

    def test_get_loss_costs(self):
        """CA16: cost of each loss exposed for other modules (Kaizen)."""
        self._log_time("mrp.block_reason1", 30)
        losses = self.CostLine._get_loss_costs(self.company, self.date_from, self.date_to, product=self.product)
        self.assertEqual(set(losses), {"scrap", "stoppage", "changeover", "energy", "waste"})
        self.assertAlmostEqual(losses["stoppage"]["amount"], 30.0, 2)
        self.assertAlmostEqual(losses["stoppage"]["per_unit"], 6.0, 2)
