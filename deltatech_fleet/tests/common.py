# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class FleetCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tz="Europe/Bucharest"))
        brand = cls.env["fleet.vehicle.model.brand"].create({"name": "Test Brand"})
        model = cls.env["fleet.vehicle.model"].create({"name": "Test Model", "brand_id": brand.id})
        cls.driver = cls.env["res.partner"].create({"name": "Test Driver"})
        cls.driver2 = cls.env["res.partner"].create({"name": "Test Backup Driver"})
        cls.vehicle = cls.env["fleet.vehicle"].create(
            {
                "model_id": model.id,
                "license_plate": "B-01-TST",
                "avg_cons": 10.0,
                "driver_id": cls.driver.id,
                "driver2_id": cls.driver2.id,
                "vehicle_category_id": cls.env.ref("deltatech_fleet.id_category_N1").id,
            }
        )
        cls.vehicle2 = cls.env["fleet.vehicle"].create(
            {"model_id": model.id, "license_plate": "B-02-TST", "avg_cons": 20.0}
        )
        cls.loc_a = cls.env["fleet.location"].create({"name": "Bucuresti"})
        cls.loc_b = cls.env["fleet.location"].create({"name": "Ploiesti"})
        cls.route = cls.env["fleet.route"].create(
            {
                "from_loc_id": cls.loc_a.id,
                "to_loc_id": cls.loc_b.id,
                "distance": 120,
                "duration": 1.5,
                "dist_c1": 100,
                "dist_c2": 10,
                "dist_c3": 10,
            }
        )
        cls.fuel_type = cls.env.ref("deltatech_fleet.type_service_service_fuel")
        # 5 oct 2026 is a Monday
        cls.day = datetime(2026, 10, 5)

    def _sheet(self, day=None, vehicle=None, **vals):
        day = day or self.day
        return self.env["fleet.map.sheet"].create(
            {
                "vehicle_id": (vehicle or self.vehicle).id,
                "date_start": day.replace(hour=6),
                "date_end": day.replace(hour=18),
                **vals,
            }
        )

    def _route_log(self, sheet, distance, hour, **vals):
        begin = sheet.date_start.replace(hour=hour)
        return self.env["fleet.route.log"].create(
            {
                "vehicle_id": sheet.vehicle_id.id,
                "map_sheet_id": sheet.id,
                "distance": distance,
                "date_begin": begin,
                "date_end": begin + timedelta(hours=1),
                **vals,
            }
        )

    def _fuel_log(self, liter, date_time, vehicle=None, price=7.5):
        return self.env["fleet.vehicle.log.fuel"].create(
            {
                "vehicle_id": (vehicle or self.vehicle).id,
                "service_type_id": self.fuel_type.id,
                "liter": liter,
                "price_per_liter": price,
                "amount": liter * price,
                "date_time": date_time,
            }
        )
