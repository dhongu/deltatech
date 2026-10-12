# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from datetime import date, datetime

import pytz

from odoo.tests import tagged

from .common import FleetCommon


@tagged("post_install", "-at_install")
class TestFleetVehicle(FleetCommon):
    def test_act_show_map_sheet(self):
        action = self.vehicle.act_show_map_sheet()
        self.assertEqual(action["res_model"], "fleet.map.sheet")
        self.assertEqual(action["domain"], [("vehicle_id", "=", self.vehicle.id)])
        self.assertEqual(action["context"]["default_vehicle_id"], self.vehicle.id)

    def test_conv_local_datetime_to_utc(self):
        Vehicle = self.env["fleet.vehicle"]
        self.assertEqual(Vehicle._conv_local_datetime_to_utc("2026-10-05 00:00:00"), "2026-10-04 21:00:00")
        self.assertEqual(Vehicle._conv_local_datetime_to_utc(datetime(2026, 1, 5, 0, 0)), "2026-01-04 22:00:00")
        aware = pytz.utc.localize(datetime(2026, 10, 5, 8, 0))
        self.assertEqual(Vehicle._conv_local_datetime_to_utc(aware), "2026-10-05 08:00:00")
        self.env.user.tz = False
        self.assertEqual(
            Vehicle.with_context(tz=False)._conv_local_datetime_to_utc("2026-10-05 00:00:00"),
            "2026-10-05 00:00:00",
        )

    def test_odometer_date_and_date_time_in_sync(self):
        odometer = self.env["fleet.vehicle.odometer"].create(
            {"vehicle_id": self.vehicle.id, "value": 1000, "date": "2026-10-01"}
        )
        odometer.write({"date": "2026-10-02"})
        self.assertEqual(odometer.date_time, datetime(2026, 10, 2))
        odometer.write({"date_time": "2026-10-03 10:00:00"})
        self.assertEqual(odometer.date, date(2026, 10, 3))

    def test_reservoir_level_without_vehicle(self):
        Level = self.env["fleet.reservoir.level"]
        self.assertEqual(Level.get_level(False), 0)
        self.assertEqual(Level.get_level_to(self.env["fleet.vehicle"], self.day), 0)
        self.assertEqual(self.vehicle2.reservoir_level, 0)
