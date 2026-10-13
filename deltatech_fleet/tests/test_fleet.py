# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestFleet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.vehicle_brand = cls.env["fleet.vehicle.model.brand"].create({"name": "Test Brand"})
        cls.vehicle_model = cls.env["fleet.vehicle.model"].create(
            {"name": "Test Model", "brand_id": cls.vehicle_brand.id}
        )
        cls.vehicle_category = cls.env.ref("deltatech_fleet.id_category_N1")

        cls.vehicle = cls.env["fleet.vehicle"].create(
            {
                "model_id": cls.vehicle_model.id,
                "license_plate": "Test Plate",
                "odometer": 1000,
                "avg_cons": 10.0,
                "vehicle_category_id": cls.vehicle_category.id,
            }
        )
        cls.location_a = cls.env["fleet.location"].create({"name": "Test Location A"})
        cls.location_b = cls.env["fleet.location"].create({"name": "Test Location B"})
        cls.route = cls.env["fleet.route"].create(
            {
                "from_loc_id": cls.location_a.id,
                "to_loc_id": cls.location_b.id,
                "distance": 120,
                "duration": 1.5,
            }
        )

    def _create_fuel_log(self, liter, date_time):
        return self.env["fleet.vehicle.log.fuel"].create(
            {
                "vehicle_id": self.vehicle.id,
                "service_type_id": self.env.ref("deltatech_fleet.type_service_service_fuel").id,
                "liter": liter,
                "price_per_liter": 7.5,
                "amount": liter * 7.5,
                "date_time": date_time,
            }
        )

    def test_fleet(self):
        sheet = Form(self.env["fleet.map.sheet"])
        sheet.vehicle_id = self.vehicle
        sheet.date_start = fields.Datetime.now()
        with sheet.route_log_ids.new() as route:
            route.distance = 150

        sheet = sheet.save()
        self.assertEqual(sheet.category_id, self.vehicle_category)
        self.assertEqual(sheet.distance_total, 150)

    def test_reservoir_level(self):
        self.assertEqual(self.vehicle.reservoir_level, 0)
        self._create_fuel_log(50, fields.Datetime.now() - timedelta(hours=1))
        self.vehicle.invalidate_recordset(["reservoir_level"])
        self.assertEqual(self.vehicle.reservoir_level, 50)

    def test_route_reverse_and_name(self):
        self.assertEqual(self.route.name, "Test Location A-Test Location B")
        self.route.button_create_reverse()
        self.assertTrue(self.route.reverse)
        self.assertEqual(self.route.reverse.from_loc_id, self.location_b)
        self.assertEqual(self.route.reverse.to_loc_id, self.location_a)

    def test_map_sheet_flow(self):
        date_start = fields.Datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(hours=12)
        sheet = self.env["fleet.map.sheet"].create(
            {
                "vehicle_id": self.vehicle.id,
                "date_start": date_start,
                "date_end": date_end,
            }
        )
        fuel_log = self._create_fuel_log(40, date_start + timedelta(hours=1))
        route_log = self.env["fleet.route.log"].create(
            {
                "vehicle_id": self.vehicle.id,
                "route_id": self.route.id,
                "date_begin": date_start + timedelta(hours=2),
                "date_end": date_start + timedelta(hours=4),
                "distance": 120,
            }
        )
        sheet.action_get_log_fuel()
        sheet.action_get_route_log()
        self.assertEqual(fuel_log.map_sheet_id, sheet)
        self.assertEqual(route_log.map_sheet_id, sheet)
        self.assertEqual(sheet.liter_total, 40)
        self.assertEqual(sheet.distance_total, 120)
        self.assertEqual(sheet.norm_cons, 12)

        sheet.action_open()
        self.assertEqual(sheet.state, "open")
        sheet.action_done()
        self.assertEqual(sheet.state, "done")
        self.assertEqual(fuel_log.state, "done")

        report = self.env["ir.actions.report"]._render_qweb_html(
            "deltatech_fleet.fleet_map_sheet_list_report", sheet.ids
        )
        self.assertTrue(report[0])

        copy = sheet.copy()
        self.assertEqual(copy.date_start, sheet.date_start + timedelta(days=1))

    def test_map_sheet_constraints(self):
        now = fields.Datetime.now()
        with self.assertRaises(ValidationError):
            self.env["fleet.map.sheet"].create(
                {"vehicle_id": self.vehicle.id, "date_start": now, "date_end": now - timedelta(hours=1)}
            )
        sheet = self.env["fleet.map.sheet"].create(
            {"vehicle_id": self.vehicle.id, "date_start": now, "date_end": now + timedelta(hours=1)}
        )
        with self.assertRaises(UserError):
            sheet.action_done()

    def test_cost_report(self):
        self._create_fuel_log(30, fields.Datetime.now())
        lines = self.env["fleet.vehicle.cost.report"].search_read(
            [("vehicle_id", "=", self.vehicle.id)], ["vehicle_type", "cost", "cost_type_id"]
        )
        self.assertTrue(lines)

    def test_distance_report(self):
        self._create_fuel_log(30, fields.Datetime.now())
        wizard = self.env["fleet.distance.report"].create({})
        action = wizard.button_show_report()
        self.assertEqual(action["res_model"], "fleet.distance.report.line")
