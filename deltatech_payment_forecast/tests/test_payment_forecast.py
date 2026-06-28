# Copyright (c) 2024-now Terrabit Solutions All Rights Reserved


from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentForecast(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.due_date = fields.Date.to_date("2030-05-17")
        cls.env.user.group_ids = [(4, cls.env.ref("deltatech_payment_forecast.payment_forecast_manager").id)]
        cls.partner_a.write(
            {
                "country_id": cls.env.ref("base.ro").id,
                "state_id": cls.env.ref("base.RO_B").id,
                "city": "Bucuresti",
                "street": "Str. Test 1",
                "zip": "010101",
            }
        )
        cls.product_x = cls.env["product.product"].create(
            {"name": "Test A", "type": "service", "standard_price": 100, "list_price": 150, "taxes_id": False}
        )
        cls.product_y = cls.env["product.product"].create(
            {"name": "Test B", "type": "service", "standard_price": 70, "list_price": 150, "taxes_id": False}
        )
        cls.invoice_a = cls._create_invoice()
        cls.invoice_b = cls._create_invoice()

    @classmethod
    def _create_invoice(cls):
        invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_date": cls.due_date,
                "invoice_date_due": cls.due_date,
                "invoice_line_ids": [
                    (0, 0, {"product_id": cls.product_x.id, "quantity": 1, "price_unit": 150, "tax_ids": []}),
                    (0, 0, {"product_id": cls.product_y.id, "quantity": 1, "price_unit": 150, "tax_ids": []}),
                ],
            }
        )
        invoice.action_post()
        return invoice

    def test_wizard_forecast(self):
        wizard = self.env["payment.forecast.wizard"].create({"date_to": self.due_date})

        wizard.get_forecast_lines()
        # se verifica suma totala pe data
        forecast_lines = self.env["payment.forecast"].search([])
        total = sum(forecast_lines.mapped("move_amount_residual"))
        self.assertEqual(total, 600)
