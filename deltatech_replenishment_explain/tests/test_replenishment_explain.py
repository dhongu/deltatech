from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestReplenishmentExplainDiagram(TransactionCase):
    """Unit tests for the pure-arithmetic SVG geometry of the explanation diagram.

    _explain_diagram_geometry touches no records, so it runs on an empty recordset.
    """

    def setUp(self):
        super().setUp()
        self.Op = self.env["stock.warehouse.orderpoint"]

    def _geo(self, **kw):
        base = dict(
            forecast=2.0,
            min_qty=5.0,
            max_qty=10.0,
            target=10.0,
            below_min=True,
            total_delay=7,
            horizon_days=3,
        )
        base.update(kw)
        return self.Op._explain_diagram_geometry(**base)

    def test_coordinates_inside_track(self):
        g = self._geo()
        for key in ("forecast_x", "min_x", "max_x", "lead_x", "horizon_x"):
            self.assertGreaterEqual(g[key], g["x0"], key)
            self.assertLessEqual(g[key], g["x1"], key)

    def test_to_order_gap_when_below_min(self):
        g = self._geo(below_min=True, forecast=2.0, target=10.0)
        self.assertGreater(g["to_order_w"], 0.0)
        self.assertAlmostEqual(g["to_order_x"], g["forecast_x"])

    def test_no_gap_when_not_below_min(self):
        g = self._geo(below_min=False)
        self.assertEqual(g["to_order_w"], 0.0)

    def test_min_below_max_ordering(self):
        g = self._geo(min_qty=5.0, max_qty=10.0)
        self.assertLessEqual(g["min_x"], g["max_x"])

    def test_timeline_is_monotonic(self):
        g = self._geo(total_delay=7, horizon_days=3)
        self.assertLessEqual(g["today_x"], g["lead_x"])
        self.assertLessEqual(g["lead_x"], g["horizon_x"])

    def test_zero_horizon_does_not_divide_by_zero(self):
        g = self._geo(total_delay=0, horizon_days=0)
        self.assertEqual(g["lead_x"], g["today_x"])

    def test_negative_forecast_clamped_to_left_edge(self):
        g = self._geo(forecast=-4.0)
        self.assertAlmostEqual(g["forecast_x"], g["x0"])
        self.assertEqual(g["forecast_w"], 0.0)
