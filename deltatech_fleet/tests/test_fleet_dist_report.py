# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from datetime import date

from odoo.tests import tagged

from .common import FleetCommon


@tagged("post_install", "-at_install")
class TestFleetDistanceReport(FleetCommon):
    def _odometer(self, value, day):
        return self.env["fleet.vehicle.odometer"].create({"vehicle_id": self.vehicle.id, "value": value, "date": day})

    def _wizard(self):
        return self.env["fleet.distance.report"].create({"date_from": "2026-10-01", "date_to": "2026-10-31"})

    def test_default_period_is_current_month(self):
        values = self.env["fleet.distance.report"].default_get(["date_from", "date_to"])
        today = date.today()
        self.assertEqual(values["date_from"], today.replace(day=1).isoformat())
        self.assertTrue(values["date_to"] >= today.isoformat())

    def test_cost_per_km(self):
        # readings around the period: 1000 km on 30 Sep and 1500 km on 1 Nov
        self._odometer(1000, "2026-09-30")
        self._odometer(1500, "2026-11-01")
        fuel = self._fuel_log(50, self.day.replace(hour=8))
        fuel.date = "2026-10-05"
        wizard = self._wizard()
        self.assertEqual(wizard.get_distance(self.vehicle.id), 500)
        action = wizard.button_show_report()
        line = self.env["fleet.distance.report.line"].search(action["domain"] + [("vehicle_id", "=", self.vehicle.id)])
        # 375 lei / 500 km
        self.assertRecordValues(line, [{"cost": 375, "distance": 500, "price": 0.75}])

    def test_distance_from_readings_inside_period(self):
        self._odometer(1000, "2026-10-03")
        self._odometer(1300, "2026-10-20")
        self.assertEqual(self._wizard().get_distance(self.vehicle.id), 300)
        self.assertEqual(self._wizard().get_distance(self.vehicle2.id), 0)
