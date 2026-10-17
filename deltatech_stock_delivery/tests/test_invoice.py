# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInvoice(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_salesman")
        cls.partner_a = cls.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": cls.partner_a.id})]
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Test A",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Test B",
                "is_storable": True,
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )

    def test_purchase(self):
        form_purchase = Form(self.env["purchase.order"])
        form_purchase.partner_id = self.partner_a
        with form_purchase.order_line.new() as po_line:
            po_line.product_id = self.product_a
            po_line.product_qty = 10
            po_line.price_unit = 10

        po = form_purchase.save()
        po.button_confirm()

        self.picking = po.picking_ids[0]

        # se confirma primirea produselor
        for move in self.picking.move_ids:
            if move.product_id == self.product_a:
                move._set_quantity_done(10)

        # se valideaza primirea
        self.picking.button_validate()

        po.action_create_invoice()

        invoice = po.invoice_ids
        invoice.invoice_date = "2021-01-01"
        invoice.action_post()
        action = invoice.invoice_print_delivery()
        self.assertEqual(action["res_id"], self.picking.id)

    def test_sale(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product_b, self.env.ref("stock.stock_location_stock"), 10
        )
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [(0, 0, {"product_id": self.product_b.id, "product_uom_qty": 2})],
            }
        )
        so.action_confirm()

        picking = so.picking_ids
        picking.move_ids._set_quantity_done(2)
        picking.button_validate()

        invoice = so._create_invoices()
        invoice.action_post()
        action = invoice.invoice_print_delivery()
        self.assertEqual(action["res_id"], picking.id)

    def test_no_delivery(self):
        invoice = self.init_invoice("out_invoice", partner=self.partner_a, products=self.product_a, post=True)
        with self.assertRaises(UserError):
            invoice.invoice_print_delivery()

    def test_button_visibility(self):
        """The Delivery button shows on customer documents, Reception on vendor ones."""
        arch = self.env["account.move"].get_view(view_type="form")["arch"]
        buttons = etree.fromstring(arch).xpath("//button[@name='invoice_print_delivery']")
        expressions = {}
        for button in buttons:
            label = "".join(button.itertext()).strip()
            expressions[label] = button.get("invisible")
        self.assertEqual(set(expressions), {"Delivery", "Reception"})
        expected_visible = {
            "Delivery": {"out_invoice", "out_refund"},
            "Reception": {"in_invoice", "in_refund"},
        }
        for label, expression in expressions.items():
            for move_type in ("out_invoice", "out_refund", "in_invoice", "in_refund", "entry"):
                visible = not safe_eval(expression, {"move_type": move_type})
                self.assertEqual(
                    visible,
                    move_type in expected_visible[label],
                    f"{label} button visibility for {move_type}",
                )
