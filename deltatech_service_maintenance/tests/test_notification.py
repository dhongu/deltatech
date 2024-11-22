# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import Form

from .common import TestServiceBase


class TestServiceNotification(TestServiceBase):
    def setUp(self):
        super().setUp()
        self.user_demo = self.env.user.copy()

    def test_create_notification(self):
        notification = Form(self.env["service.notification"])
        notification.partner_id = self.partner
        notification.contact_id = self.partner
        notification.work_center_id = self.work_center
        notification.service_location_id = self.location
        notification.user_id = self.user_demo
        notification = notification.save()

        notification.action_assign()
        notification.action_start()
        notification.action_order()
        notification.action_done()
        notification.new_sale_order_button()
        notification.new_delivery_button()

    def test_equipment_button(self):
        self.equipment.notification_button()
        self.equipment.order_button()

    def test_location_button(self):
        self.location.notification_button()
        self.location.order_button()

    def test_sale_order(self):
        sale_order = Form(self.env["sale.order"])
        sale_order.partner_id = self.partner
        with sale_order.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 1

        sale_order = sale_order.save()
        sale_order.new_notification()

        sale_order.action_confirm()

        picking = sale_order.picking_ids
        picking.action_assign()

    def test_create_warranty(self):
        notification = Form(self.env["service.warranty"].with_context(default_type="warranty"))
        notification.user_id = self.user_demo
        notification.partner_id = self.partner
        notification = notification.save()
        operation_type = self.env.ref("stock.picking_type_out")
        self.env["ir.config_parameter"].sudo().set_param(
            "service.picking_type_for_warranty", operation_type.id or False
        )
        notification.set_assigned()
        notification.set_in_progress()
        notification.new_delivery_button()
        notification.request_approval()

    def test_create_recondition(self):
        notification = Form(self.env["service.warranty"].with_context(default_type="recondition"))
        notification.user_id = self.user_demo
        notification = notification.save()
        notification.rec_state = "done"
