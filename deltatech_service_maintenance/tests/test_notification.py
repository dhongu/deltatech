# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form

from .common import TestServiceBase


class TestServiceNotification(TestServiceBase):
    def setUp(self):
        super(TestServiceNotification, self).setUp()

    def test_create_notification(self):
        notification = Form(self.env["service.notification"])
        notification.partner_id = self.partner
        notification.contact_id = self.partner
        notification.work_center_id = self.work_center
        notification.service_location_id = self.location
        notification.user_id = self.env.user
        notification = notification.save()
        notification.action_assign()
        notification.action_start()
        notification.action_order()
        notification.action_done()
        notification.new_sale_order_button()

    def test_equipment_button(self):
        self.equipment.notification_button()
        self.equipment.order_button()

    def test_location_button(self):
        self.location.notification_button()
        self.location.order_button()
