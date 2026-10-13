# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from datetime import datetime

from odoo.tests import tagged

from .common import FleetCommon


@tagged("post_install", "-at_install")
class TestFleetMapSheetOdometer(FleetCommon):
    def _odometer(self, value, day):
        return self.env["fleet.vehicle.odometer"].create({"vehicle_id": self.vehicle.id, "value": value, "date": day})

    def _readings(self):
        self.env.flush_all()
        return self.env["fleet.vehicle.odometer"].search([("vehicle_id", "=", self.vehicle.id)])

    def test_reading_the_sheet_does_not_create_odometers(self):
        self._odometer(1000, "2026-10-01")
        sheet = self._sheet()
        self._route_log(sheet, 120, 7)
        for _i in range(2):
            sheet.invalidate_recordset(["odometer_start", "odometer_end"])
            self.assertEqual((sheet.odometer_start, sheet.odometer_end), (1000, 1120))
        self.assertEqual(self._readings().mapped("value"), [1000])

    def test_no_reading_at_all(self):
        sheet = self._sheet()
        self._route_log(sheet, 120, 7)
        self.assertEqual((sheet.odometer_start, sheet.odometer_end), (0, 120))

    def test_end_from_later_reading(self):
        self._odometer(1000, "2026-10-01")
        self._odometer(1300, "2026-10-10")
        sheet = self._sheet()
        self._route_log(sheet, 120, 7)
        self.assertEqual((sheet.odometer_start, sheet.odometer_end), (1000, 1300))

    def test_start_given_creates_and_updates_reading(self):
        sheet = self._sheet()
        self._route_log(sheet, 120, 7)
        sheet.odometer_start = 1000
        reading = sheet.odometer_start_id
        self.assertRecordValues(reading, [{"value": 1000, "date": self.day.date(), "vehicle_id": self.vehicle.id}])
        sheet.odometer_start = 1010
        self.assertEqual(sheet.odometer_start_id, reading)
        self.assertEqual(reading.value, 1010)
        sheet.invalidate_recordset(["odometer_end"])
        # the start reading of the same day is not taken as end reading
        self.assertEqual(sheet.odometer_end, 1130)

    def test_end_given_creates_and_updates_reading(self):
        sheet = self._sheet()
        self._route_log(sheet, 40, 7)
        sheet.odometer_end = 2000
        reading = sheet.odometer_end_id
        self.assertEqual(reading.value, 2000)
        sheet.odometer_end = 2010
        self.assertEqual(sheet.odometer_end_id, reading)
        sheet.invalidate_recordset(["odometer_start"])
        # the end reading of the same day is not taken as start reading
        self.assertEqual(sheet.odometer_start, 1970)
        self.assertEqual(len(self._readings()), 1)

    def test_continuity_between_sheets(self):
        sheet1 = self._sheet()
        self._route_log(sheet1, 120, 7)
        self._route_log(sheet1, 80, 10)
        sheet1.odometer_start = 1000
        sheet1.odometer_end = 1200
        sheet2 = self._sheet(day=datetime(2026, 10, 6))
        self._route_log(sheet2, 50, 7)
        self.assertEqual((sheet2.odometer_start, sheet2.odometer_end), (1200, 1250))
        self.assertEqual(sorted(self._readings().mapped("value")), [1000, 1200])

    def test_read_odometer_buttons(self):
        sheet = self._sheet()
        self._route_log(sheet, 120, 7)
        self._odometer(1000, "2026-10-01")
        sheet.action_read_odometer_start()
        sheet.action_read_odometer_end()
        self.assertEqual((sheet.odometer_start, sheet.odometer_end), (1000, 1120))
