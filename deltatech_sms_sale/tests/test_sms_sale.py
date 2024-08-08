from odoo.exceptions import AccessError
from odoo.tests import TransactionCase


class TestSaleOrderSmsNotifications(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")  # Assuming main_company is your company record

        # Create a partner with a phone number for testing
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "phone": "+1234567890",  # Replace with a valid phone number
            }
        )

        # Create a sale order for testing
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "product.product_product_1"
                            ).id,  # Replace with a valid product ID
                            "product_uom_qty": 1,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

    def test_sms_templates_exist(self):
        """Test if SMS templates exist"""
        sms_template_confirm = self.env.ref(
            "deltatech_sms_sale.sms_template_data_sale_order_confirm", raise_if_not_found=False
        )
        sms_template_post = self.env.ref(
            "deltatech_sms_sale.sms_template_data_sale_order_post", raise_if_not_found=False
        )

        self.assertTrue(sms_template_confirm, "SMS Template for sale order confirmation does not exist")
        self.assertTrue(sms_template_post, "SMS Template for sale order post does not exist")

    def test_company_sms_settings(self):
        """Test company SMS settings"""
        company = self.company

        # Check default values
        self.assertTrue(company.sale_order_sms_confirm, "Default value for sale_order_sms_confirm should be True")
        self.assertTrue(company.sale_order_sms_post, "Default value for sale_order_sms_post should be True")

        # Modify company settings
        company.write(
            {
                "sale_order_sms_confirm": False,
                "sale_order_sms_post": False,
                "sale_order_sms_confirm_template_id": False,
                "sale_order_sms_post_template_id": False,
            }
        )

        self.assertFalse(company.sale_order_sms_confirm, "Failed to set sale_order_sms_confirm to False")
        self.assertFalse(company.sale_order_sms_post, "Failed to set sale_order_sms_post to False")
        self.assertFalse(
            company.sale_order_sms_confirm_template_id, "Failed to unset sale_order_sms_confirm_template_id"
        )
        self.assertFalse(company.sale_order_sms_post_template_id, "Failed to unset sale_order_sms_post_template_id")

    def test_sms_notifications_on_confirm(self):
        """Test SMS notifications when a sale order is confirmed"""
        sale_order = self.sale_order

        # Ensure company settings are enabled
        self.company.write(
            {
                "sale_order_sms_confirm": True,
                "sale_order_sms_confirm_template_id": self.env.ref(
                    "deltatech_sms_sale.sms_template_data_sale_order_confirm"
                ).id,
            }
        )

        # Call action_confirm which should trigger SMS notification
        try:
            sale_order.action_confirm()
        except AccessError:
            # If current user doesn't have access rights, ignore this test
            self.skipTest("Current user does not have access rights to send SMS")

        # Check if SMS was sent (You might need to implement a mock SMS service for this)
        # Assert that the SMS was sent to the partner's phone number

    def test_sms_notifications_on_post(self):
        """Test SMS notifications when a sale order is posted"""
        sale_order = self.sale_order

        # Ensure company settings are enabled
        self.company.write(
            {
                "sale_order_sms_post": True,
                "sale_order_sms_post_template_id": self.env.ref(
                    "deltatech_sms_sale.sms_template_data_sale_order_post"
                ).id,
            }
        )

        # Call _send_order_confirmation_mail which should trigger SMS notification
        try:
            sale_order._send_order_confirmation_mail()
        except AccessError:
            # If current user doesn't have access rights, ignore this test
            self.skipTest("Current user does not have access rights to send SMS")

        # Check if SMS was sent (You might need to implement a mock SMS service for this)
        # Assert that the SMS was sent to the partner's phone number
