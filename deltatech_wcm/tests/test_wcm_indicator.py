# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWcmIndicator(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Pillar = cls.env["wcm.pillar"]
        cls.Indicator = cls.env["wcm.indicator"]
        cls.test_pillar = cls.Pillar.create({"name": "Test pillar", "code": "test_pillar"})

    def _manual(self, pillar=None, direction="higher", target=80, warning=50, value=None):
        indicator = self.Indicator.create(
            {
                "name": "Manual test",
                "pillar_id": (pillar or self.test_pillar).id,
                "source": "manual",
                "direction": direction,
                "target": target,
                "warning": warning,
            }
        )
        if value is not None:
            indicator.write({"manual_value": value, "manual_date": "2026-01-15"})
        return indicator

    def test_seed_pillars(self):
        """CA1: the ten WCM pillars exist in the WCM order."""
        pillars = self.Pillar.search([("code", "!=", "test_pillar")], order="sequence, id")
        self.assertEqual(
            pillars.mapped("name"),
            [
                "Safety",
                "Cost Deployment",
                "Focused Improvement",
                "Autonomous Maintenance",
                "Planned Maintenance",
                "Quality Control",
                "Logistics and Customer Service",
                "Early Equipment Management",
                "People Development",
                "Environment and Energy",
            ],
        )

    def test_placeholder_manual_indicators(self):
        """CA2: Safety and Focused Improvement are manual placeholders."""
        for code in ("safety", "focused_improvement"):
            pillar = self.env["wcm.pillar"].search([("code", "=", code)])
            self.assertTrue(pillar.indicator_ids, f"pillar {code} has no placeholder indicator")
            self.assertEqual(set(pillar.indicator_ids.mapped("source")), {"manual"})

    def test_state_higher(self):
        """CA3: higher is better: green at/above target, yellow at/above warning, red below."""
        indicator = self._manual(direction="higher", target=80, warning=50, value=90)
        self.assertEqual(indicator.state, "green")
        indicator.manual_value = 80
        self.assertEqual(indicator.state, "green")
        indicator.manual_value = 60
        self.assertEqual(indicator.state, "yellow")
        indicator.manual_value = 50
        self.assertEqual(indicator.state, "yellow")
        indicator.manual_value = 40
        self.assertEqual(indicator.state, "red")

    def test_state_lower(self):
        """CA4: lower is better: green at/below target, yellow at/below warning, red above."""
        indicator = self._manual(direction="lower", target=2, warning=5)
        indicator.manual_date = "2026-01-15"
        indicator.manual_value = 1
        self.assertEqual(indicator.state, "green")
        indicator.manual_value = 2
        self.assertEqual(indicator.state, "green")
        indicator.manual_value = 3
        self.assertEqual(indicator.state, "yellow")
        indicator.manual_value = 5
        self.assertEqual(indicator.state, "yellow")
        indicator.manual_value = 6
        self.assertEqual(indicator.state, "red")

    def test_no_data_state(self):
        """CA5: an indicator without a value shows no data, not green or red."""
        indicator = self._manual(direction="higher", target=80, warning=50)
        self.assertFalse(indicator.has_data)
        self.assertEqual(indicator.state, "none")
        # A manual value without a date is still no data.
        indicator.manual_value = 95
        self.assertFalse(indicator.has_data)
        self.assertEqual(indicator.state, "none")

    def test_pillar_worst_state(self):
        """CA6: a pillar shows the worst state of its indicators."""
        pillar = self.Pillar.create({"name": "Worst state", "code": "worst_state"})
        self.assertEqual(pillar.state, "none")
        self._manual(pillar=pillar, value=90)  # green
        self.assertEqual(pillar.state, "green")
        self._manual(pillar=pillar, value=60)  # yellow
        self.assertEqual(pillar.state, "yellow")
        self._manual(pillar=pillar, value=10)  # red
        self.assertEqual(pillar.state, "red")
        self.assertEqual((pillar.green_count, pillar.yellow_count, pillar.red_count), (1, 1, 1))
        self._manual(pillar=pillar)  # no data does not hide the red
        self.assertEqual(pillar.state, "red")
        self.assertEqual(pillar.indicator_count, 4)

    def test_warning_consistency(self):
        """CA7: a warning that contradicts the direction is refused."""
        with self.assertRaises(ValidationError):
            self._manual(direction="higher", target=80, warning=90)
        with self.assertRaises(ValidationError):
            self._manual(direction="lower", target=2, warning=1)

    def test_live_sources_empty(self):
        """CA8: live sources return no data when the period has no data."""
        for source in ("oee", "mtbf", "mttr", "control_fail", "scrap", "on_time"):
            indicator = self.Indicator.create(
                {
                    "name": f"Live {source}",
                    "pillar_id": self.test_pillar.id,
                    "source": source,
                    "target": 50,
                    "warning": 50,
                }
            )
            self.assertFalse(indicator.has_data, f"source {source} should have no data on an empty database")
            self.assertEqual(indicator.state, "none")

    def test_access_user_read_only(self):
        """CA10: a plant user reads the dashboard but cannot change targets."""
        user = self.env["res.users"].create(
            {
                "name": "WCM reader",
                "login": "wcm_reader",
                "group_ids": [(6, 0, [self.env.ref("mrp.group_mrp_user").id])],
            }
        )
        indicator = self._manual(value=90)
        self.assertEqual(indicator.with_user(user).state, "green")
        with self.assertRaises(AccessError):
            indicator.with_user(user).write({"target": 10})
