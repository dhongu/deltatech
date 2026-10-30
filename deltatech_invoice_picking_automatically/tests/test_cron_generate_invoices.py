# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.deltatech_invoice_picking_automatically.models.stock_picking import StockPicking


@tagged("post_install", "-at_install")
class TestCronGenerateInvoices(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "is_storable": True,
                "invoice_policy": "delivery",
                "list_price": 100.0,
            }
        )
        warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        warehouse.out_type_id.create_invoice_automatically = True
        cls.env["stock.quant"]._update_available_quantity(cls.product, warehouse.lot_stock_id, 10)

    def _create_delivered_picking(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1})],
            }
        )
        order.action_confirm()
        picking = order.picking_ids
        picking.move_ids.quantity = 1
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.invoice_state, "to_invoice")
        return picking

    def test_failed_picking_does_not_abort_batch(self):
        bad_picking = self._create_delivered_picking()
        good_picking = self._create_delivered_picking()
        original = StockPicking._generate_invoice_automatically

        def _generate(picking):
            if picking == bad_picking:
                # a real SQL error leaves the transaction aborted without a savepoint
                picking.env.cr.execute("SELECT 1/0")
            return original(picking)

        with (
            patch.object(StockPicking, "_generate_invoice_automatically", _generate),
            self.assertLogs("odoo.addons.deltatech_invoice_picking_automatically.models.stock_picking", "ERROR"),
        ):
            self.env["stock.picking"].search([("id", "not in", (bad_picking | good_picking).ids)]).write(
                {"invoice_state": False}
            )
            self.env["stock.picking"]._cron_generate_invoices()

        self.assertEqual(bad_picking.invoice_state, "failed")
        self.assertFalse(bad_picking.sale_id.invoice_ids)
        self.assertIn("Automatic invoicing failed", bad_picking.message_ids[0].body)
        self.assertEqual(good_picking.invoice_state, "invoiced")
        self.assertEqual(good_picking.sale_id.invoice_ids.state, "posted")
