# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form

from .common import TestServiceBase


class TestServiceOrder(TestServiceBase):
    def setUp(self):
        super().setUp()
        self.order_type = self.env["service.order.type"].create(
            {
                "name": "Test Order Type",
            }
        )

    def test_create_order(self):
        service_order = Form(self.env["service.order"])
        service_order.partner_id = self.partner
        service_order.contact_id = self.partner
        service_order.work_center_id = self.work_center
        service_order.service_location_id = self.location
        service_order.type_id = self.order_type
        service_order = service_order.save()

        service_order.new_sale_order_button()
        service_order.new_delivery_button()
