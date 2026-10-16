# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestInvoiceDelivery(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # the cost stays under every tested net price, so that margin checks of other modules
        # (deltatech_sale_margin, deltatech_sale_commission) installed in the same database pass
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Test A", "is_storable": True, "standard_price": 50, "list_price": 150}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Test B", "is_storable": True, "standard_price": 50, "list_price": 150}
        )
        cls.service = cls.env["product.product"].create({"name": "Test Service", "type": "service"})
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.env["stock.quant"]._update_available_quantity(cls.product_a, cls.stock_location, 1000)
        cls.env["stock.quant"]._update_available_quantity(cls.product_b, cls.stock_location, 1000)
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.journal.invoice_delivery = True

    def _create_invoice(self, lines, journal=None, invoice_date=None):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": (journal or self.journal).id,
                "invoice_date": invoice_date or fields.Date.today(),
                "invoice_line_ids": [
                    (0, 0, {"product_id": product.id, "quantity": qty, "price_unit": price, "discount": discount})
                    for product, qty, price, discount in lines
                ],
            }
        )

    def _sale_order(self, invoice):
        return self.env["sale.order"].search([("from_invoice_id", "=", invoice.id)])

    def test_invoice_creates_confirmed_order_and_delivery(self):
        invoice = self._create_invoice([(self.product_a, 5, 150, 10)])
        invoice.action_post()

        self.assertEqual(invoice.state, "posted")
        order = self._sale_order(invoice)
        self.assertEqual(len(order), 1)
        self.assertEqual(order.state, "sale")
        self.assertEqual(order.picking_ids.mapped("state"), ["done"])
        self.assertEqual(order.order_line.qty_delivered, 5)
        self.assertEqual(order.order_line.qty_invoiced, 5)
        self.assertEqual(self.product_a.with_context(location=self.stock_location.id).qty_available, 995)

    def test_discount_and_taxes_reach_the_order(self):
        invoice = self._create_invoice([(self.product_a, 5, 100, 10)])
        invoice.action_post()

        order = self._sale_order(invoice)
        self.assertAlmostEqual(order.order_line.discount, 10)
        self.assertAlmostEqual(order.order_line.price_subtotal, invoice.invoice_line_ids.price_subtotal)
        self.assertEqual(order.order_line.tax_ids, invoice.invoice_line_ids.tax_ids)

    def test_journal_without_option_keeps_standard_flow(self):
        journal = self.journal.copy({"name": "Sales without delivery", "code": "SNDL", "invoice_delivery": False})
        invoice = self._create_invoice([(self.product_a, 5, 150, 0)], journal=journal)
        invoice.action_post()

        self.assertEqual(invoice.state, "posted")
        self.assertFalse(self._sale_order(invoice))
        self.assertEqual(self.product_a.with_context(location=self.stock_location.id).qty_available, 1000)

    def test_service_lines_are_not_ordered(self):
        invoice = self._create_invoice([(self.product_a, 1, 150, 0), (self.service, 1, 50, 0)])
        invoice.action_post()

        order = self._sale_order(invoice)
        self.assertEqual(order.order_line.product_id, self.product_a)
        service_line = invoice.invoice_line_ids.filtered(lambda line: line.product_id == self.service)
        self.assertFalse(service_line.sale_line_ids)

    def test_not_enough_stock_blocks_posting(self):
        invoice = self._create_invoice([(self.product_a, 5000, 150, 0)])
        with self.assertRaisesRegex(UserError, "available"), self.env.cr.savepoint():
            invoice.action_post()

        self.assertEqual(invoice.state, "draft")
        self.assertFalse(self._sale_order(invoice))

    def test_negative_quantity_returns_to_stock(self):
        invoice = self._create_invoice([(self.product_a, 10, 150, 0), (self.product_b, -10, 150, 0)])
        invoice.action_post()

        self.assertEqual(invoice.state, "posted")
        order = self._sale_order(invoice)
        self.assertTrue(all(state == "done" for state in order.picking_ids.mapped("state")))
        self.assertEqual(self.product_a.with_context(location=self.stock_location.id).qty_available, 990)
        self.assertEqual(self.product_b.with_context(location=self.stock_location.id).qty_available, 1010)

    def test_multi_step_delivery_is_refused(self):
        self.warehouse.delivery_steps = "pick_ship"
        invoice = self._create_invoice([(self.product_a, 1, 150, 0)])
        with self.assertRaisesRegex(UserError, "one step"), self.env.cr.savepoint():
            invoice.action_post()

        self.assertEqual(invoice.state, "draft")

    def test_invoice_form_context_does_not_reach_the_delivery(self):
        # Posted from the invoice form, the context carries default_move_type, also a field of stock.picking
        invoice = self._create_invoice([(self.product_a, 3, 150, 0), (self.product_b, -1, 150, 0)])
        invoice.with_context(default_move_type="out_invoice", default_journal_id=self.journal.id).action_post()

        self.assertEqual(invoice.state, "posted")
        pickings = self._sale_order(invoice).picking_ids
        self.assertTrue(all(state == "done" for state in pickings.mapped("state")))
        self.assertTrue(all(move_type in ("direct", "one") for move_type in pickings.mapped("move_type")))
