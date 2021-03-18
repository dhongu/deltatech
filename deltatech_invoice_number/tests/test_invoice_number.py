# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestInvoiceNumer(TransactionCase):
    def setUp(self):
        super(TestInvoiceNumer, self).setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"name": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {"name": "Test A", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )
        self.product_b = self.env["product.product"].create(
            {"name": "Test B", "type": "product", "standard_price": 70, "list_price": 150, "seller_ids": seller_ids}
        )
        self.stock_location = self.env["ir.model.data"].xmlid_to_object("stock.stock_location_stock")
        inv_line_a = {
            "product_id": self.product_a.id,
            "product_qty": 10000,
            "location_id": self.stock_location.id,
        }
        inv_line_b = {
            "product_id": self.product_b.id,
            "product_qty": 10000,
            "location_id": self.stock_location.id,
        }
        inventory = self.env["stock.inventory"].create(
            {
                "name": "Inv. productserial1",
                "line_ids": [
                    (0, 0, inv_line_a),
                    (0, 0, inv_line_b),
                ],
            }
        )
        inventory.action_start()
        inventory.action_validate()

    def test_invoice_number(self):
        invoice = Form(self.env["account.move"].with_context(default_move_type="out_invoice"))
        invoice.partner_id = self.partner_a

        with invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_a
            line.quantity = 10
            line.price_unit = 150

        with invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_b
            line.quantity = 10
            line.price_unit = 150

        invoice = invoice.save()
        invoice.post()

        wizard = self.env["account.invoice.change.number"].with_context(active_id=invoice.id)

        wizard = Form(wizard)
        wizard.internal_number = "test_1234"
        wizard = wizard.save()
        wizard.do_change_number()

    def test_action_get_number(self):
        invoice = Form(self.env["account.move"].with_context(default_move_type="out_invoice"))
        invoice.partner_id = self.partner_a

        with invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_a
            line.quantity = 10
            line.price_unit = 150

        with invoice.invoice_line_ids.new() as line:
            line.product_id = self.product_b
            line.quantity = 10
            line.price_unit = 150

        invoice.invoice_date = "2099-01-01"
        invoice = invoice.save()
        invoice.journal_id.journal_sequence_id = self.env["ir.sequence"].create({"name": "test"})
        invoice.action_get_number()
