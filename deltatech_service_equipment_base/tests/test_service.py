# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestService(TransactionCase):
    def setUp(self):
        super().setUp()
        self.meter_category = self.env["service.meter.category"].create(
            {
                "name": "Test Meter Category",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )
        self.equipment_type = self.env["service.equipment.type"].create(
            {
                "name": "Test Equipment Type",
            }
        )
        self.equipment_model = self.env["service.equipment.model"].create(
            {
                "name": "Test Equipment Model",
            }
        )

    def test_create_equipment(self):
        equipment = Form(self.env["service.equipment"])
        equipment.name = "Test Equipment"
        equipment.type_id = self.equipment_type
        equipment.model_id = self.equipment_model
        equipment = equipment.save()

        meter = Form(self.env["service.meter"])
        meter.name = "Test Meter"
        meter.meter_categ_id = self.meter_category
        meter.equipment_id = equipment
        meter = meter.save()

        meter_reading = Form(self.env["service.meter.reading"])
        meter_reading.meter_id = meter
        meter_reading.counter_value = 100
        meter_reading.date = "2020-01-01"
        meter_reading.save()

        meter_reading = Form(self.env["service.meter.reading"])
        meter_reading.meter_id = meter
        meter_reading.counter_value = 200
        meter_reading.date = "2020-01-02"
        meter_reading.save()

        wizard_enter_readings = Form(self.env["service.enter.reading"].with_context(active_ids=[equipment.id]))
        wizard_enter_readings.date = "2020-01-03"
        wizard_enter_readings = wizard_enter_readings.save()
        wizard_enter_readings.do_enter()

        meter.calc_forecast_coef()
        meter.recheck_value()

    def test_create_location(self):
        location = Form(self.env["service.location"])
        location.name = "Test Location"
        location = location.save()
