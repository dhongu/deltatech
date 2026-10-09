# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestInvoicePickingAutomatically(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Partner
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

        # Product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
                "invoice_policy": "delivery",
            }
        )

        # Warehouse and picking type with create_invoice_automatically
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.picking_type_out.write(
            {
                "create_invoice_automatically": True,
                "post_invoice_automatically": True,
            }
        )

    def _create_sale_order(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        return sale_order

    def _confirm_and_validate_picking(self, sale_order):
        sale_order.action_confirm()
        picking = sale_order.picking_ids[0]
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()
        return picking

    def test_invoice_state_set_on_done(self):
        """La validarea picking-ului, invoice_state trebuie setat pe 'to_invoice'."""
        sale_order = self._create_sale_order()
        picking = self._confirm_and_validate_picking(sale_order)
        self.assertEqual(
            picking.invoice_state,
            "to_invoice",
            "invoice_state trebuie sa fie 'to_invoice' dupa validarea picking-ului",
        )

    def test_cron_generates_and_posts_invoice(self):
        """Cronul trebuie sa genereze si sa posteze factura, si sa marcheze picking-ul ca 'invoiced'."""
        sale_order = self._create_sale_order()
        picking = self._confirm_and_validate_picking(sale_order)
        self.assertEqual(picking.invoice_state, "to_invoice")

        # Rulam cronul
        self.env["stock.picking"]._cron_generate_invoices()

        self.assertEqual(
            picking.invoice_state,
            "invoiced",
            "invoice_state trebuie sa fie 'invoiced' dupa rularea cronului",
        )

        invoices = sale_order.invoice_ids
        self.assertTrue(invoices, "Trebuie sa existe cel putin o factura generata")
        self.assertTrue(
            all(inv.state == "posted" for inv in invoices),
            "Toate facturile trebuie sa fie postate (post_invoice_automatically=True)",
        )

    def test_cron_no_invoice_when_flag_disabled(self):
        """Daca create_invoice_automatically=False, picking-ul nu trebuie sa aiba invoice_state setat."""
        self.picking_type_out.write({"create_invoice_automatically": False})
        try:
            sale_order = self._create_sale_order()
            picking = self._confirm_and_validate_picking(sale_order)
            self.assertFalse(
                picking.invoice_state,
                "invoice_state nu trebuie setat daca create_invoice_automatically=False",
            )
        finally:
            self.picking_type_out.write({"create_invoice_automatically": True})

    def test_cron_invoice_not_posted_when_post_disabled(self):
        """Daca post_invoice_automatically=False, factura trebuie sa ramana in draft."""
        self.picking_type_out.write({"post_invoice_automatically": False})
        try:
            sale_order = self._create_sale_order()
            picking = self._confirm_and_validate_picking(sale_order)
            self.assertEqual(picking.invoice_state, "to_invoice")

            self.env["stock.picking"]._cron_generate_invoices()

            invoices = sale_order.invoice_ids
            self.assertTrue(invoices, "Trebuie sa existe cel putin o factura generata")
            self.assertTrue(
                all(inv.state == "draft" for inv in invoices),
                "Facturile trebuie sa ramana in draft daca post_invoice_automatically=False",
            )
        finally:
            self.picking_type_out.write({"post_invoice_automatically": True})

    def _run_cron_with_failing_post(self, fail_partner, failure):
        """Run the cron while posting the invoices of ``fail_partner`` raises."""
        move_class = type(self.env["account.move"])
        original_post = move_class.action_post

        def action_post(moves):
            if fail_partner in moves.partner_id:
                failure(moves)
            return original_post(moves)

        with (
            patch.object(move_class, "action_post", action_post),
            mute_logger("odoo.addons.deltatech_invoice_picking_automatically.models.stock_picking", "odoo.sql_db"),
        ):
            self.env["stock.picking"]._cron_generate_invoices()

    def _assert_isolated_failure(self, good_order, good_picking, bad_order, bad_picking):
        self.assertEqual(good_picking.invoice_state, "invoiced")
        self.assertTrue(good_order.invoice_ids)
        self.assertEqual(set(good_order.invoice_ids.mapped("state")), {"posted"})

        self.assertEqual(bad_picking.invoice_state, "failed")
        self.assertFalse(bad_order.invoice_ids, "The failed invoicing must not leave a draft invoice")
        self.assertFalse(
            self.env["account.move"].search([("partner_id", "=", bad_order.partner_id.id)]),
            "No orphan invoice may remain for the failed picking",
        )
        self.assertFalse(bad_order.order_line.invoice_lines)
        self.assertEqual(bad_order.order_line.qty_invoiced, 0.0)
        self.assertEqual(bad_order.invoice_status, "to invoice")

    def _create_two_pickings(self):
        good_order = self._create_sale_order()
        good_picking = self._confirm_and_validate_picking(good_order)
        bad_partner = self.env["res.partner"].create({"name": "Test Partner Failing"})
        bad_order = self._create_sale_order()
        bad_order.partner_id = bad_partner
        bad_picking = self._confirm_and_validate_picking(bad_order)
        return good_order, good_picking, bad_order, bad_picking

    def test_cron_validation_error_rolls_back_only_failed_picking(self):
        """A posting error rolls back the draft of that picking; the other one is invoiced."""
        good_order, good_picking, bad_order, bad_picking = self._create_two_pickings()

        def failure(moves):
            raise UserError(moves.env._("Posting blocked for test"))

        self._run_cron_with_failing_post(bad_order.partner_id, failure)
        self._assert_isolated_failure(good_order, good_picking, bad_order, bad_picking)

    def test_cron_sql_error_does_not_abort_transaction(self):
        """A database error in one invoicing does not abort the cron transaction."""
        good_order, good_picking, bad_order, bad_picking = self._create_two_pickings()

        def failure(moves):
            moves.env.cr.execute("SELECT 1/0")

        self._run_cron_with_failing_post(bad_order.partner_id, failure)
        self._assert_isolated_failure(good_order, good_picking, bad_order, bad_picking)
