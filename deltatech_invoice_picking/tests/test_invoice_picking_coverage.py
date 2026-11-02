# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInvoicePickingCoverage(TransactionCase):
    """The to invoice flag of a transfer follows the cumulative invoiced quantities."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Coverage Partner"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Test Coverage A", "is_storable": True, "list_price": 100.0}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Test Coverage B", "is_storable": True, "list_price": 50.0}
        )
        warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        for product in cls.product_a | cls.product_b:
            cls.env["stock.quant"]._update_available_quantity(product, warehouse.lot_stock_id, 100.0)

    def _sale_order(self, products):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": p.id, "product_uom_qty": 10.0}) for p in products],
            }
        )
        order.action_confirm()
        return order

    def _validate(self, picking):
        picking.move_ids.quantity = 10.0
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertTrue(picking.to_invoice)

    def _invoice(self, order, quantities):
        """Invoice the order lines with the given quantities, in the given order, as _create_invoices does."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "quantity": qty,
                            "price_unit": product.list_price,
                            "sale_line_ids": [
                                (6, 0, order.order_line.filtered(lambda sl, p=product: sl.product_id == p).ids)
                            ],
                        },
                    )
                    for product, qty in quantities
                ],
            }
        )
        invoice.update_pickings()
        return invoice

    def test_partial_line_not_cleared_by_full_line(self):
        for quantities in (
            [(self.product_a, 5.0), (self.product_b, 10.0)],
            [(self.product_b, 10.0), (self.product_a, 5.0)],
        ):
            order = self._sale_order(self.product_a | self.product_b)
            picking = order.picking_ids
            self._validate(picking)
            invoice = self._invoice(order, quantities)
            self.assertEqual(picking.account_move_id, invoice)
            self.assertTrue(picking.to_invoice, "Product A is only half invoiced")

    def test_sequential_partial_invoices(self):
        order = self._sale_order(self.product_a)
        picking = order.picking_ids
        self._validate(picking)
        self._invoice(order, [(self.product_a, 5.0)])
        self.assertTrue(picking.to_invoice)
        invoice_2 = self._invoice(order, [(self.product_a, 5.0)])
        self.assertEqual(picking.account_move_id, invoice_2)
        self.assertFalse(picking.to_invoice, "The two invoices cover the whole delivery")

    def test_cancelled_invoice_reset_to_draft_relinks_picking(self):
        order = self._sale_order(self.product_a)
        picking = order.picking_ids
        self._validate(picking)
        invoice = self._invoice(order, [(self.product_a, 10.0)])
        self.assertFalse(picking.to_invoice)
        invoice.button_cancel()
        self.assertTrue(picking.to_invoice)
        self.assertFalse(picking.account_move_id)
        invoice.button_draft()
        self.assertEqual(picking.account_move_id, invoice)
        self.assertFalse(picking.to_invoice)

    def test_batch_keeps_partially_invoiced_picking(self):
        Batch = self.env["stock.picking.batch"]
        order = self._sale_order(self.product_a)
        picking = order.picking_ids
        # the batch is formed before validation: _sanity_check refuses done transfers
        batch = Batch.create({"picking_ids": [(6, 0, picking.ids)]})
        self._validate(picking)
        self.assertEqual(batch.state, "done")
        self._invoice(order, [(self.product_a, 5.0)])
        self.assertTrue(picking.account_move_id)
        self.assertTrue(picking.to_invoice)

        batch.invalidate_recordset(["invoiced"])
        self.assertFalse(batch.invoiced)
        self.assertIn(batch, Batch.search([("invoiced", "=", False)]))
        self.assertNotIn(batch, Batch.search([("invoiced", "=", True)]))
        action = batch.action_create_invoice()
        self.assertEqual(action["context"]["picking_ids"], picking.ids)
