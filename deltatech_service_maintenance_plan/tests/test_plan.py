# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPlan(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        self.cycle = self.env["service.cycle"].create(
            {
                "name": "Test Cycle",
                "value": 1,
                "unit": "month",
            }
        )
        self.work_center = self.env["service.work.center"].create(
            {
                "name": "Test Work Order",
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

        self.equipment = self.env["service.equipment"].create(
            {
                "name": "Test Equipment",
                "type_id": self.equipment_type.id,
                "model_id": self.equipment_model.id,
            }
        )
        self.location = self.env["service.location"].create(
            {
                "name": "Test Location",
            }
        )
        self.order_type = self.env["service.order.type"].create(
            {
                "name": "Test Order Type",
            }
        )

    def test_plan(self):
        plan = Form(self.env["service.plan"])
        plan.cycle_id = self.cycle
        plan.work_center_id = self.work_center
        plan.order_type_id = self.order_type
        plan.equipment_id = self.equipment
        plan.service_location_id = self.location

        plan = plan.save()
        plan.action_start()
        plan.action_stop()
        plan.action_restart()
        plan.last_call_id.order_id.action_done()
        plan.last_call_id.action_complete()
        plan.rescheduling()
        plan.last_call_id.action_skip()
        plan.rescheduling()

        self.last_call_done = plan.equipment_id.last_call_done
        self.last_call_done = plan.service_location_id.last_call_done
