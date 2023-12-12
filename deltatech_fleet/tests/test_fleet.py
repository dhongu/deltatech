# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestFleet(TransactionCase):
    def setUp(self):
        super().setUp()

        self.vehicle_brand = self.env["fleet.vehicle.model.brand"].create({"name": "Test Brand"})
        self.vehicle_model = self.env["fleet.vehicle.model"].create(
            {"name": "Test Model", "brand_id": self.vehicle_brand.id}
        )

        self.vehicle = self.env["fleet.vehicle"].create(
            {"model_id": self.vehicle_model.id, "license_plate": "Test Plate", "odometer": 1000}
        )
        self.location = self.env["fleet.location"].create({"name": "Test Location"})
        self.route = self.env["fleet.route"].create({"from_loc_id": self.location.id, "to_loc_id": self.location.id})

    def test_fleet(self):
        sheet = Form(self.env["fleet.map.sheet"])
        sheet.vehicle_id = self.vehicle
        sheet.date_start = fields.Datetime.now()
        with sheet.route_log_ids.new() as route:
            route.distance = 150

        sheet.save()

    def test_reservoir_level(self):
        self.reservoir_level = self.vehicle.reservoir_level
