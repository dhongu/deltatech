# Copyright (c) 2024-now Terrabit Solutions All Rights Reserved


import datetime

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPaymentForecast(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        self.product_a = self.env["product.product"].create(
            {"name": "Test A", "type": "service", "standard_price": 100, "list_price": 150, "taxes_id": False}
        )
        self.product_b = self.env["product.product"].create(
            {"name": "Test B", "type": "service", "standard_price": 70, "list_price": 150, "taxes_id": False}
        )

        self.journal = self.env["account.journal"].create({"name": "Sales", "type": "sale", "code": "INV"})

        invoice = Form(self.env["account.move"].with_context(default_move_type="out_invoice"))
        invoice.partner_id = self.partner_a
        invoice.invoice_date_due = datetime.datetime(2030, 5, 17)

        with invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_a
            line.quantity = 1
            line.price_unit = 150

        with invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_b
            line.quantity = 1
            line.price_unit = 150

        self.invoice_a = invoice.save()
        self.invoice_a.action_post()

        invoice = Form(self.env["account.move"].with_context(default_move_type="out_invoice"))
        invoice.partner_id = self.partner_a
        invoice.invoice_date_due = datetime.datetime(2030, 5, 17)

        with invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_a
            line.quantity = 1
            line.price_unit = 150

        with invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_b
            line.quantity = 1
            line.price_unit = 150

        self.invoice_b = invoice.save()
        self.invoice_b.action_post()

    def test_wizard_forecast(self):
        wizard = self.env["payment.forecast.wizard"].create(
            {
                "date_to": datetime.datetime(2030, 5, 17),
            }
        )

        wizard.get_forecast_lines()
        # se verifica suma totala pe data
        forecast_lines = self.env["payment.forecast"].search([])
        total = 0.0
        for line in forecast_lines:
            total += line.move_amount_residual
        self.assertEqual(total, 600)
