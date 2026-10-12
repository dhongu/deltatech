# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from datetime import datetime, timedelta

from odoo import fields
from odoo.tests import Form, tagged

from .common import FleetCommon


@tagged("post_install", "-at_install")
class TestFleetMapSheet(FleetCommon):
    def test_norm_cons_and_reservoir(self):
        # 120 km + 80 km at 10 l/100 km = 12 l + 8 l; 50 l fuelled before departure,
        # so the fuel log stays outside the sheet but counts in the reservoir
        sheet = self._sheet()
        self._route_log(sheet, 120, 7)
        self._route_log(sheet, 80, 10)
        fuel = self._fuel_log(50, self.day.replace(hour=5))
        sheet.action_get_log_fuel()
        self.env.flush_all()
        self.assertRecordValues(
            sheet,
            [
                {
                    "distance_total": 200,
                    "norm_cons": 20,
                    "liter_total": 0,
                    "amount_total": 0,
                    "reservoir_level_start": 50,
                    "reservoir_level_end": 30,
                }
            ],
        )
        self.assertFalse(fuel.map_sheet_id)
        self.assertEqual(self.vehicle.reservoir_level, 30)

    def test_reservoir_level_sees_unflushed_route_logs(self):
        self._fuel_log(50, self.day.replace(hour=5))
        sheet = self._sheet()
        self.env.flush_all()
        route_log = self._route_log(sheet, 100, 7)
        route_log.distance = 200  # 20 l, still pending in the ORM
        sheet.invalidate_recordset(["reservoir_level_end"])
        self.assertEqual(sheet.reservoir_level_end, 30)
        self.vehicle.invalidate_recordset(["reservoir_level"])
        self.assertEqual(self.vehicle.reservoir_level, 30)

    def test_norm_cons_follows_distance_and_vehicle(self):
        sheet = self._sheet()
        route_log = self._route_log(sheet, 100, 7)
        self.assertEqual(route_log.norm_cons, 10)
        route_log.distance = 200
        self.assertEqual(route_log.norm_cons, 20)
        self.assertEqual(sheet.norm_cons, 20)
        route_log.vehicle_id = self.vehicle2
        self.assertEqual(route_log.norm_cons, 40)
        route_log.vehicle_id = False
        self.assertEqual(route_log.norm_cons, 0)

    def test_route_log_equivalent_distance_and_week_day(self):
        sheet = self._sheet()
        route_log = self._route_log(sheet, 120, 7, dist_c1=100, dist_c2=10, dist_c3=10)
        # 100 + 1.1 * 10 + 1.4 * 10
        self.assertAlmostEqual(route_log.dist_echiv, 125)
        self.assertEqual(route_log.name, "Noname")
        self.assertEqual(route_log.week_day, 1)
        sunday = self._route_log(self._sheet(day=datetime(2026, 10, 11)), 10, 7, route_id=self.route.id)
        self.assertEqual(sunday.week_day, 0)
        self.assertEqual(sunday.name, "Bucuresti-Ploiesti")
        self.assertEqual(self.env["fleet.route.log"].new({}).week_day, 0)

    def test_states(self):
        sheet = self._sheet()
        self._route_log(sheet, 120, 7)
        fuel = self._fuel_log(40, self.day.replace(hour=8))
        sheet.action_get_log_fuel()
        self.assertTrue(sheet.button_dummy())
        sheet.action_open()
        self.assertEqual(sheet.state, "open")
        sheet.action_done()
        self.assertEqual(sheet.state, "done")
        self.assertEqual(fuel.state, "done")

    def test_fuel_and_route_outside_sheet_are_not_taken(self):
        sheet = self._sheet()
        fuel_other_day = self._fuel_log(40, self.day + timedelta(days=1))
        fuel_other_vehicle = self._fuel_log(40, self.day.replace(hour=8), vehicle=self.vehicle2)
        route_log = self.env["fleet.route.log"].create(
            {
                "vehicle_id": self.vehicle.id,
                "distance": 10,
                "date_begin": self.day.replace(hour=17),
                "date_end": self.day.replace(hour=19),
            }
        )
        sheet.action_get_log_fuel()
        sheet.action_get_route_log()
        self.assertFalse(fuel_other_day.map_sheet_id)
        self.assertFalse(fuel_other_vehicle.map_sheet_id)
        self.assertFalse(route_log.map_sheet_id)

    def test_copy(self):
        sheet = self._sheet()
        self._fuel_log(40, self.day.replace(hour=8))
        sheet.action_get_log_fuel()
        copy = sheet.copy()
        self.assertNotEqual(copy.name, sheet.name)
        self.assertEqual(copy.date, sheet.date + timedelta(days=1))
        self.assertEqual(copy.date_start, sheet.date_start + timedelta(days=1))
        self.assertEqual(copy.date_end, sheet.date_end + timedelta(days=1))
        self.assertFalse(copy.log_fuel_ids)

    def test_default_dates_from_context(self):
        # Europe/Bucharest is UTC+3 in October
        sheet = self.env["fleet.map.sheet"].with_context(date="2026-10-05").create({"vehicle_id": self.vehicle.id})
        self.assertEqual(sheet.date, fields.Date.to_date("2026-10-05"))
        self.assertEqual(sheet.date_start, datetime(2026, 10, 4, 21, 0, 0))
        self.assertEqual(sheet.date_end, datetime(2026, 10, 5, 20, 59, 59))

    def test_default_dates_without_timezone(self):
        self.env.user.tz = False
        sheet = (
            self.env["fleet.map.sheet"]
            .with_context(date="2026-10-05", tz=False)
            .create({"vehicle_id": self.vehicle.id})
        )
        self.assertEqual(sheet.date_start, datetime(2026, 10, 5, 0, 0, 0))
        self.assertEqual(sheet.date_end, datetime(2026, 10, 5, 23, 59, 59))

    def test_default_route_log_begin_after_previous_routes(self):
        sheet = self._sheet()
        first = self._route_log(sheet, 10, 7)  # ends at 08:00
        second = self._route_log(sheet, 10, 8)  # ends at 09:00
        RouteLog = self.env["fleet.route.log"].with_context(
            date="2026-10-05 06:00:00",
            route_log_ids=[
                (4, first.id),
                (0, 0, {"date_end": "2026-10-05 11:00:00"}),
                (1, second.id, {"distance": 20}),
            ],
        )
        values = RouteLog.default_get(["date_begin", "date_end"])
        self.assertEqual(values["date_begin"], datetime(2026, 10, 5, 11, 0, 0))
        self.assertEqual(values["date_end"], datetime(2026, 10, 5, 11, 0, 0))
        self.assertFalse(self.env["fleet.route.log"].default_get(["date_begin"]).get("date_begin"))

    def test_onchange_vehicle_sets_drivers(self):
        form = Form(self.env["fleet.map.sheet"])
        form.vehicle_id = self.vehicle
        self.assertEqual(form.driver_id, self.driver)
        self.assertEqual(form.driver2_id, self.driver2)

    def test_onchange_date_start_moves_draft_routes(self):
        sheet = self._sheet()
        sheet.date_start_old = sheet.date_start
        draft = self._route_log(sheet, 10, 7)
        done = self._route_log(sheet, 10, 9, state="done")
        form = Form(sheet)
        form.date_start = sheet.date_start + timedelta(hours=1)
        form.save()
        self.assertEqual(draft.date_begin, self.day.replace(hour=8))
        self.assertEqual(draft.date_end, self.day.replace(hour=9))
        self.assertEqual(done.date_begin, self.day.replace(hour=9))

    def test_onchange_route_logs_extend_date_end(self):
        form = Form(self.env["fleet.map.sheet"])
        form.vehicle_id = self.vehicle
        form.date_start = self.day.replace(hour=6)
        form.date_end = self.day.replace(hour=18)
        with form.route_log_ids.new() as route_log:
            route_log.date_begin = self.day.replace(hour=5)
            route_log.date_end = self.day.replace(hour=20)
            route_log.distance = 50
        self.assertEqual(form.date_end, self.day.replace(hour=20))
        sheet = form.save()
        self.assertEqual(sheet.distance_total, 50)
        self.assertEqual(sheet.route_log_ids.vehicle_id, self.vehicle)

    def test_onchange_route_fills_route_log(self):
        form = Form(self.env["fleet.route.log"])
        form.vehicle_id = self.vehicle
        form.date_begin = self.day.replace(hour=7)
        form.route_id = self.route
        self.assertEqual(form.date_end, self.day.replace(hour=8, minute=30))
        self.assertEqual(form.distance, 120)
        self.assertEqual(form.save().norm_cons, 12)
        # road class distances are not on the route log form, only in the map sheet lines
        route_log = self.env["fleet.route.log"].new({"date_begin": self.day.replace(hour=7), "route_id": self.route.id})
        route_log.on_change_route()
        self.assertEqual((route_log.dist_c1, route_log.dist_c2, route_log.dist_c3), (100, 10, 10))

    def test_print_map_sheet(self):
        sheet = self._sheet(driver_id=self.driver.id)
        self._route_log(sheet, 120, 7, route_id=self.route.id)
        self._fuel_log(40, self.day.replace(hour=8))
        sheet.action_get_log_fuel()
        html = (
            self.env["ir.actions.report"]
            ._render_qweb_html("deltatech_fleet.fleet_map_sheet_list_report", sheet.ids)[0]
            .decode()
        )
        self.assertIn(sheet.name, html)
        self.assertIn("Bucuresti-Ploiesti", html)
        self.assertIn("Test Driver", html)
