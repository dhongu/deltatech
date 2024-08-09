from datetime import datetime, timedelta

from odoo import fields
from odoo.tests import TransactionCase


class TestPurchaseOrderReminder(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create test data
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Supplier",
            }
        )

        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )

        self.supplier_info = self.env["product.supplierinfo"].create(
            {
                "name": self.partner.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "delay": 5,
            }
        )
        self.user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
            }
        )

        self.purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "date_planned": datetime.now() + timedelta(days=4),
                "user_id": self.user.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_qty": 1,
                            "price_unit": 100.0,
                            "date_planned": datetime.now() + timedelta(days=10),
                        },
                    )
                ],
            }
        )

        # Create a test activity type
        self.activity_type = self.env["mail.activity.type"].create(
            {
                "name": "Test Reminder Activity",
                "summary": "Test Summary",
                "category": "default",
            }
        )

        # Set the configuration parameter
        self.env["ir.config_parameter"].sudo().set_param(
            "deltatech_purchase_confirmation_reminder.purchase_order_reminder_activity_type_id",
            self.activity_type.id,
        )

    def test_action_send_reminder(self):
        self.env["res.config.settings"].create({})
        # Ensure the purchase order is in draft state
        self.assertEqual(self.purchase_order.state, "draft", "Purchase order should be in 'draft' state")

        # Simulate running the action
        self.purchase_order.action_send_reminder()

        # Fetch the reminder activity created
        activity = self.env["mail.activity"].search(
            [
                ("res_id", "=", self.purchase_order.id),
                ("res_model_id", "=", self.env["ir.model"]._get("purchase.order").id),
                ("summary", "=", "Purchase Order Reminder"),
            ],
            limit=1,
        )

        # Check if the reminder activity was created
        self.assertTrue(activity, "No reminder activity was created.")
        self.assertEqual(
            activity.user_id,
            self.purchase_order.user_id,
            "The activity should be assigned to the purchase order's user.",
        )
        self.assertEqual(activity.date_deadline, fields.Date.today(), "The activity deadline should be today's date.")
