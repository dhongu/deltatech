# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
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

    def _validate(self, picking, qty, backorder=True):
        """Validate ``picking`` with ``qty`` done, as the user does (backorder dialog included)."""
        picking.move_ids.quantity = qty
        res = picking.button_validate()
        if isinstance(res, dict) and res.get("res_model") == "stock.backorder.confirmation":
            wizard = Form(self.env["stock.backorder.confirmation"].with_context(**res["context"])).save()
            if backorder:
                wizard.process()
            else:
                wizard.process_cancel_backorder()
        return picking

    # invoicing from the quantities of the transfer (#4033)

    def test_each_delivery_gets_its_own_invoice(self):
        """Two deliveries of the same order: one invoice each, with the quantity of the delivery."""
        sale_order = self._create_sale_order()
        sale_order.action_confirm()
        picking = self._validate(sale_order.picking_ids, 1)
        self.env["stock.picking"]._cron_generate_invoices()
        backorder = sale_order.picking_ids - picking
        self._validate(backorder, 1)
        self.env["stock.picking"]._cron_generate_invoices()
        self.assertEqual((picking | backorder).mapped("invoice_state"), ["invoiced", "invoiced"])
        self.assertEqual(len(sale_order.invoice_ids), 2)
        self.assertEqual(sale_order.invoice_ids.mapped("invoice_line_ids.quantity"), [1.0, 1.0])
        self.assertEqual(picking.account_move_id | backorder.account_move_id, sale_order.invoice_ids)

    def test_customer_return_gets_a_credit_note(self):
        sale_order = self._create_sale_order()
        delivery = self._confirm_and_validate_picking(sale_order)
        self.env["stock.picking"]._cron_generate_invoices()
        self.warehouse.in_type_id.create_invoice_automatically = True
        return_picking = delivery._create_return()
        return_picking.picking_type_id.create_invoice_automatically = True
        self._validate(return_picking, 1)
        self.env["stock.picking"]._cron_generate_invoices()
        self.assertEqual(return_picking.invoice_state, "invoiced")
        refund = sale_order.invoice_ids.filtered(lambda i: i.move_type == "out_refund")
        self.assertEqual(refund.invoice_line_ids.quantity, 1.0)
        self.assertEqual(refund.state, "posted")

    def test_receipt_gets_a_draft_vendor_bill(self):
        """A receipt of a purchase gets a vendor bill in draft, even with the posting option."""
        receipt_type = self.warehouse.in_type_id
        receipt_type.write({"create_invoice_automatically": True, "post_invoice_automatically": True})
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_qty": 3, "price_unit": 40.0})],
            }
        )
        purchase.button_confirm()
        receipt = self._validate(purchase.picking_ids, 2, backorder=False)
        self.env["stock.picking"]._cron_generate_invoices()
        self.assertEqual(receipt.invoice_state, "invoiced")
        bill = purchase.invoice_ids
        self.assertEqual(bill.move_type, "in_invoice")
        self.assertEqual(bill.state, "draft")
        self.assertEqual(bill.invoice_line_ids.quantity, 2.0)

    # invoicing on validation, failure reason and retry (#4035)

    def test_invoice_on_validation(self):
        self.picking_type_out.invoice_moment = "validation"
        sale_order = self._create_sale_order()
        picking = self._confirm_and_validate_picking(sale_order)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(picking.account_move_id, sale_order.invoice_ids)
        self.assertFalse(picking.to_invoice, "deltatech_invoice_picking must not flag it again")
        self.assertEqual(sale_order.invoice_ids.state, "posted")

    def test_failure_on_validation_keeps_the_transfer_done_and_can_be_retried(self):
        self.picking_type_out.invoice_moment = "validation"
        sale_order = self._create_sale_order()
        move_class = type(self.env["account.move"])
        original_post = move_class.action_post

        def failing_post(moves):
            raise UserError(moves.env._("Posting blocked for test"))

        with (
            patch.object(move_class, "action_post", failing_post),
            mute_logger("odoo.addons.deltatech_invoice_picking_automatically.models.stock_picking", "odoo.sql_db"),
        ):
            picking = self._confirm_and_validate_picking(sale_order)
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.invoice_state, "failed")
        self.assertEqual(picking.invoice_error, "Posting blocked for test")
        self.assertFalse(sale_order.invoice_ids)
        self.assertEqual(self.env["stock.picking"].search([("invoice_state", "=", "failed")]), picking)
        # the cause is fixed: the retry invoices it
        self.assertTrue(original_post)
        picking.action_retry_auto_invoice()
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertFalse(picking.invoice_error)
        self.assertEqual(sale_order.invoice_ids.state, "posted")

    def test_warehouse_user_without_invoicing_rights(self):
        self.picking_type_out.invoice_moment = "validation"
        user = self.env["res.users"].create(
            {
                "name": "Warehouse User",
                "login": "tb_warehouse_user",
                "group_ids": [(6, 0, [self.env.ref("stock.group_stock_user").id])],
            }
        )
        self.assertFalse(user.has_group("account.group_account_invoice"))
        sale_order = self._create_sale_order()
        sale_order.action_confirm()
        picking = sale_order.picking_ids.with_user(user)
        picking.move_ids.quantity = 2
        picking.button_validate()
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(sale_order.invoice_ids.state, "posted")

    # transfers without an order do not stay in the queue (#3583)

    def test_transfer_without_order_is_not_queued(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "partner_id": self.partner.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "location_id": self.picking_type_out.default_location_src_id.id,
                            "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.quantity = 1
        picking.button_validate()
        self.assertFalse(picking.invoice_state)

    def test_queued_transfer_without_order_leaves_the_queue(self):
        """A transfer queued before this fix, without an order, fails with a reason instead of blocking."""
        picking = self.env["stock.picking"].create(
            {"picking_type_id": self.picking_type_out.id, "invoice_state": "to_invoice"}
        )
        with mute_logger("odoo.addons.deltatech_invoice_picking_automatically.models.stock_picking"):
            self.env["stock.picking"]._cron_generate_invoices()
        self.assertEqual(picking.invoice_state, "failed")
        self.assertTrue(picking.invoice_error)

    def test_receipt_already_billed_fails_with_a_reason(self):
        """A receipt with nothing left to bill fails with a reason instead of an empty vendor bill."""
        self.warehouse.in_type_id.create_invoice_automatically = True
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_qty": 1, "price_unit": 40.0})],
            }
        )
        purchase.button_confirm()
        receipt = self._validate(purchase.picking_ids, 1)
        purchase.action_create_invoice()  # billed by hand before the scheduled action
        with mute_logger("odoo.addons.deltatech_invoice_picking_automatically.models.stock_picking"):
            self.env["stock.picking"]._cron_generate_invoices()
        self.assertEqual(receipt.invoice_state, "failed")
        self.assertTrue(receipt.invoice_error)
        self.assertEqual(len(purchase.invoice_ids), 1, "No empty vendor bill is added")

    def test_receipt_already_billed_linked_by_hand_and_retried(self):
        """Linking the existing bill and clearing To invoice, then retrying, marks the receipt invoiced."""
        self.warehouse.in_type_id.create_invoice_automatically = True
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_qty": 1, "price_unit": 40.0})],
            }
        )
        purchase.button_confirm()
        receipt = self._validate(purchase.picking_ids, 1)
        purchase.action_create_invoice()
        with mute_logger("odoo.addons.deltatech_invoice_picking_automatically.models.stock_picking"):
            self.env["stock.picking"]._cron_generate_invoices()
        self.assertEqual(receipt.invoice_state, "failed")
        receipt.write({"account_move_id": purchase.invoice_ids.id, "to_invoice": False})
        receipt.action_retry_auto_invoice()
        self.assertEqual(receipt.invoice_state, "invoiced")
        self.assertFalse(receipt.invoice_error)
        self.assertEqual(len(purchase.invoice_ids), 1)
