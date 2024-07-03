# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestInvoiceDelivery(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})
        seller_ids = [(0, 0, {"partner_id": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "consu",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "type": "consu",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.stock_location = self.env.ref("stock.stock_location_stock")
        self.env["stock.quant"]._update_available_quantity(self.product_a, self.stock_location, 1000)
        self.env["stock.quant"]._update_available_quantity(self.product_b, self.stock_location, 1000)

    def create_in_invoice(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
            }
        )

        form_invoice = Form(invoice)
        form_invoice.partner_id = self.partner_a
        form_invoice.invoice_date = fields.Date.today()

        with form_invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_a
            line.quantity = 100

        with form_invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_b
            line.quantity = 100

        invoice = form_invoice.save()

        invoice.action_post()

    def test_create_invoice(self):
        self.create_in_invoice()

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
            }
        )

        form_invoice = Form(invoice)
        form_invoice.partner_id = self.partner_a
        form_invoice.invoice_date = fields.Date.today()

        with form_invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_b
            line.quantity = 100

        invoice = form_invoice.save()
        invoice.action_post()

    def test_create_invoice_with_negative_qty(self):
        Journal = self.env["account.journal"]

        Journal.create(
            {
                "name": "Test Purchase Journal",
                "code": "TPUR",
                "type": "purchase",
                "sequence": 10,
                "active": True,
            }
        )
        self.create_in_invoice()

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
            }
        )

        form_invoice = Form(invoice)
        form_invoice.partner_id = self.partner_a
        form_invoice.invoice_date = fields.Date.today()

        with form_invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_a
            line.quantity = 100

        with form_invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_b
            line.quantity = -10

        invoice = form_invoice.save()

        invoice.action_post()
