# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import Form, tagged

from .common import FleetCommon


@tagged("post_install", "-at_install")
class TestFleetFuel(FleetCommon):
    def _form(self):
        form = Form(self.env["fleet.vehicle.log.fuel"])
        form.vehicle_id = self.vehicle
        form.service_type_id = self.fuel_type
        form.date_time = self.day.replace(hour=8)
        return form

    def test_onchange_amount_from_liter_and_price(self):
        form = self._form()
        form.liter = 2
        form.price_per_liter = 1.5
        self.assertEqual(form.amount, 3.0)

    def test_onchange_price_from_amount_and_liter(self):
        form = self._form()
        form.amount = 300
        form.liter = 40
        self.assertEqual(form.price_per_liter, 7.5)

    def test_onchange_liter_from_amount_and_price(self):
        form = self._form()
        form.amount = 300
        form.price_per_liter = 7.5
        self.assertEqual(form.liter, 40)
        fuel = form.save()
        self.assertRecordValues(fuel, [{"liter": 40, "price_per_liter": 7.5, "amount": 300}])

    def test_onchange_vehicle_clears_map_sheet(self):
        sheet = self._sheet()
        fuel = self._fuel_log(40, self.day.replace(hour=8))
        fuel.map_sheet_id = sheet
        form = Form(fuel)
        form.vehicle_id = self.vehicle2
        self.assertFalse(form.map_sheet_id)

    def test_reservoir_level(self):
        self._fuel_log(50, self.day.replace(hour=5))
        later = self._fuel_log(20, self.day.replace(hour=12))
        sheet = self._sheet()
        self._route_log(sheet, 100, 7)  # 10 l
        self.env.flush_all()
        later.invalidate_recordset(["reservoir_level"])
        # 50 l + 20 l - 10 l
        self.assertEqual(later.reservoir_level, 60)
        self.assertEqual(self.env["fleet.vehicle.log.fuel"].new({}).reservoir_level, 0)
