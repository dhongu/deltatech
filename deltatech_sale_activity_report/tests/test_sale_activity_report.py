# tests/test_sale_order_activity_record.py
from datetime import datetime

from odoo.tests.common import TransactionCase


class TestSaleOrderActivityRecord(TransactionCase):
    def setUp(self):
        super().setUp()
        self.sale_order_model = self.env["sale.order"]
        self.mail_activity_model = self.env["mail.activity"]
        self.sale_order_activity_record_model = self.env["sale.order.activity.record"]
        self.user = self.env.ref("base.user_admin")
        self.partner_a = self.env["res.partner"].create({"name": "Test"})
        self.sale_order = self.sale_order_model.create(
            {
                "partner_id": self.partner_a.id,
                "state": "draft",
            }
        )

    def test_create_mail_activity(self):
        """Test that creating a mail.activity for a sale.order creates a sale.order.activity.record"""
        sale_order_model_id = self.env["ir.model"].search([("model", "=", "sale.order")], limit=1).id

        self.mail_activity_model.with_user(self.user).create(
            {
                "res_model": "sale.order",
                "res_model_id": sale_order_model_id,  # Explicitly setting res_model_id
                "res_id": self.sale_order.id,
                "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                "summary": "Test Activity",
                "user_id": self.user.id,
            }
        )

        today = datetime.now().date()
        activity_record = self.sale_order_activity_record_model.search(
            [
                ("sale_order_id", "=", self.sale_order.id),
                ("change_date", "=", today),
                ("user_id", "=", self.user.id),
            ],
            limit=1,
        )

        self.assertTrue(activity_record, "Sale Order Activity Record should be created")
        self.assertEqual(activity_record.state, self.sale_order.state, "State should match the Sale Order state")

    def test_update_sale_order(self):
        """Test that updating a sale.order creates or updates a sale.order.activity.record"""
        self.sale_order.with_user(self.user).write({"state": "sale"})

        today = datetime.now().date()
        activity_record = self.sale_order_activity_record_model.search(
            [
                ("sale_order_id", "=", self.sale_order.id),
                ("change_date", "=", today),
                ("user_id", "=", self.user.id),
            ],
            limit=1,
        )

        self.assertTrue(activity_record, "Sale Order Activity Record should be created")
        self.assertEqual(activity_record.state, "sale", "State should be updated to 'sale'")

        # Update the sale order again
        self.sale_order.with_user(self.user).write({"state": "done"})
        activity_record.invalidate_recordset()

        self.assertEqual(activity_record.state, "done", "State should be updated to 'done'")
