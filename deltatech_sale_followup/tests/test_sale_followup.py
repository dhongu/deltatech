from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo.tests.common import TransactionCase


class TestSaleFollowup(TransactionCase):
    def setUp(self):
        super().setUp()
        # Set up demo data for testing
        self.company = self.env.ref("base.main_company")
        self.template = self.env["mail.template"].create(
            {
                "name": "Test Sale Followup Template",
                "model_id": self.env.ref("sale.model_sale_order").id,
                "subject": "Followup: ${object.name}",
                "body_html": "This is a test followup email for sale order ${object.name}.",
            }
        )
        self.company.write(
            {
                "sale_followup": True,
                "sale_followup_template_id": self.template.id,
            }
        )

        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Customer",
            }
        )

        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "list_price": 100,
            }
        )

        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "date_order": date.today(),
                "days_send_followup": 5,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )

    def test_onchange_date_order(self):
        # Change date_order and verify the follow-up date updates accordingly
        new_date_order = date.today() + timedelta(days=2)
        self.sale_order.date_order = new_date_order
        self.sale_order._onchange_date_order()
        self.assertEqual(
            self.sale_order.date_send_followup, new_date_order + relativedelta(days=self.sale_order.days_send_followup)
        )

    def test_send_followup(self):
        # Manually trigger the follow-up email sending
        self.sale_order.send_followup()

        # Check if follow-up fields are reset
        self.assertFalse(self.sale_order.days_send_followup, "days_send_followup should be reset to False")
        self.assertFalse(self.sale_order.date_send_followup, "date_send_followup should be reset to False")

    def test_cron_send_followup(self):
        # Prepare the sale order for follow-up
        self.sale_order.date_send_followup = date.today()

        # Run the cron job to send follow-up emails
        self.env["sale.order"].cron_send_followup()

        # Check if follow-up fields are reset
        self.assertFalse(
            self.sale_order.days_send_followup, "days_send_followup should be reset to False by the cron job"
        )
        self.assertFalse(
            self.sale_order.date_send_followup, "date_send_followup should be reset to False by the cron job"
        )
