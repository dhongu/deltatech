# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from lxml import etree

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestInvoicePickingBatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Batch = cls.env["stock.picking.batch"]
        cls.partner = cls.env["res.partner"].create({"name": "Test Batch Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Batch Product", "is_storable": True, "list_price": 100.0}
        )
        warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.env["stock.quant"]._update_available_quantity(cls.product, warehouse.lot_stock_id, 100.0)

    def _receipt(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 5.0,
                            "price_unit": 10.0,
                            "date_planned": fields.Date.today(),
                        },
                    )
                ],
            }
        )
        order.button_confirm()
        return order.picking_ids

    def _delivery(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 2.0})],
            }
        )
        order.action_confirm()
        return order.picking_ids

    def _done_batch(self, picking, invoice_number=None):
        # the batch is formed before validation: _sanity_check refuses done transfers
        batch = self.Batch.create({"picking_ids": [(6, 0, picking.ids)]})
        picking.move_ids.quantity = picking.move_ids.product_uom_qty
        picking.move_ids.picked = True
        picking.button_validate()
        if invoice_number:
            picking.supplier_invoice_number = invoice_number
        self.assertEqual(batch.state, "done")
        return batch

    def test_batch_without_transfers_is_not_invoiced(self):
        batch = self.Batch.create({})
        self.assertFalse(batch.invoiced)
        self.assertIn(batch, self.Batch.search([("invoiced", "=", False)]))
        self.assertNotIn(batch, self.Batch.search([("invoiced", "=", True)]))

    def test_invoice_all_selected_receipt_batches(self):
        picking_1 = self._receipt()
        picking_2 = self._receipt()
        batch_1 = self._done_batch(picking_1, "TEST/BATCH/001")
        batch_2 = self._done_batch(picking_2, "TEST/BATCH/002")

        (batch_1 | batch_2).action_create_invoice()

        self.assertTrue(picking_1.account_move_id)
        self.assertTrue(picking_2.account_move_id)
        (batch_1 | batch_2).invalidate_recordset(["invoiced"])
        self.assertTrue(batch_1.invoiced)
        self.assertTrue(batch_2.invoiced)

    def test_invoice_all_selected_delivery_batches(self):
        picking_1 = self._delivery()
        picking_2 = self._delivery()
        batch_1 = self._done_batch(picking_1)
        batch_2 = self._done_batch(picking_2)

        action = (batch_1 | batch_2).action_create_invoice()

        self.assertEqual(set(action["context"]["picking_ids"]), set((picking_1 | picking_2).ids))
        self.assertEqual(set(action["context"]["active_ids"]), set((picking_1 | picking_2).sale_id.ids))

    def test_mixed_batch_types_are_refused(self):
        batch_in = self._done_batch(self._receipt(), "TEST/BATCH/003")
        batch_out = self._done_batch(self._delivery())
        with self.assertRaises(UserError):
            (batch_in | batch_out).action_create_invoice()

    def test_invoice_button_hidden_when_not_done_or_invoiced(self):
        arch = self.Batch.get_view(view_type="form")["arch"]
        button = etree.fromstring(arch).xpath("//button[@name='action_create_invoice']")
        self.assertTrue(button)
        self.assertEqual(button[0].get("invisible"), "state!='done' or invoiced")
