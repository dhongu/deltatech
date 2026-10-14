# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.binary import BinaryBytes

from .test_ubl_import import _xml_invoice


@tagged("post_install", "-at_install")
class TestUblImportFlow(TransactionCase):
    """Receipts (partial, several moves, other units) and vendor bill taxes/errors."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.Wizard = cls.env["purchase.ubl.import.wizard"]
        cls.vendor = cls.env["res.partner"].create({"name": "Flow Vendor SRL", "vat": "RO40000004", "supplier_rank": 1})
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Flow Product A",
                "default_code": "FLOW-A",
                "is_storable": True,
                "purchase_ok": True,
                "purchase_method": "purchase",
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Flow Product B",
                "default_code": "FLOW-B",
                "is_storable": True,
                "purchase_ok": True,
                "purchase_method": "purchase",
            }
        )
        Tax = cls.env["account.tax"]
        tax_vals = {"type_tax_use": "purchase", "amount_type": "percent", "company_id": cls.company.id}
        cls.tax_21 = Tax.create(dict(tax_vals, name="FLOW Purchase 21%", amount=21))
        cls.tax_11 = Tax.create(dict(tax_vals, name="FLOW Purchase 11%", amount=11))

    def _order(self, lines, confirm=True):
        """lines: list of (product, qty) or (product, qty, uom)"""
        order_lines = []
        for spec in lines:
            product, qty = spec[0], spec[1]
            uom = spec[2] if len(spec) > 2 else product.uom_id
            order_lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_qty": qty,
                        "price_unit": 10.0,
                        "name": product.name,
                        "uom_id": uom.id,
                        "date_planned": "2025-01-01 00:00:00",
                        "tax_ids": [(6, 0, self.tax_21.ids)],
                    },
                )
            )
        order = self.env["purchase.order"].create(
            {"partner_id": self.vendor.id, "company_id": self.company.id, "order_line": order_lines}
        )
        if confirm:
            order.button_confirm()
        return order

    def _import(self, order, lines, invoice_id="", **vals):
        xml = _xml_invoice(
            invoice_id=invoice_id,
            order_ref=order.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[dict({"price": "10", "unit_code": "C62", "tax": "21"}, **line) for line in lines],
        )
        wizard = self.Wizard.with_context(active_model="purchase.order", active_id=order.id).create(
            dict(
                {
                    "data_file": BinaryBytes(xml),
                    "update_prices": False,
                    "create_missing_products": False,
                },
                **vals,
            )
        )
        wizard.action_import()
        return wizard

    # ------------------------------------------------------------------
    # Receipts
    # ------------------------------------------------------------------
    def test_partial_receipt_creates_backorder(self):
        """3 of 5 units of A received, B and an unknown line absent from the receipt."""
        order = self._order([(self.product_a, 5.0), (self.product_b, 2.0)])
        wizard = self._import(
            order,
            [
                {"code": "FLOW-A", "name": self.product_a.name, "qty": "3"},
                {"code": "FLOW-UNKNOWN", "name": "Flow Unknown", "qty": "1"},
            ],
            validate_receipt=True,
        )
        line_a = order.order_line.filtered(lambda line: line.product_id == self.product_a)
        line_b = order.order_line.filtered(lambda line: line.product_id == self.product_b)
        self.assertEqual(line_a.qty_received, 3.0)
        self.assertEqual(line_b.qty_received, 0.0)
        # B is not on the invoice, so its order line keeps the ordered quantity
        self.assertEqual(line_b.product_qty, 2.0)
        backorder = order.picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))
        self.assertTrue(backorder, "The rest of the receipt goes to a backorder")
        self.assertIn("Receipt updated", wizard.log)
        self.assertIn("Unmatched lines in the order: FLOW-UNKNOWN", wizard.log)
        self.assertTrue(wizard.has_warning)

    def test_receipt_split_over_two_moves_of_same_product(self):
        """2 units on a product ordered as 3 + 3: the first move takes them, the second none."""
        order = self._order([(self.product_a, 3.0), (self.product_a, 3.0)])
        picking = order.picking_ids
        self.assertEqual(len(picking.move_ids), 2)
        allocation = self.Wizard._allocate_receipt_quantities(picking.move_ids, {self.product_a.id: 2.0})
        self.assertEqual(list(allocation.values()), [2.0])

    def test_receipt_quantity_in_move_unit(self):
        """A move in dozens receives the invoiced units converted to dozens."""
        dozen = self.env.ref("uom.product_uom_dozen")
        order = self._order([(self.product_a, 12.0)])
        move = order.picking_ids.move_ids
        move.write({"uom_id": dozen.id, "product_uom_qty": 1.0})
        self.assertEqual(self.Wizard._receipt_qty_in_move_uom(move, {self.product_a.id: 12.0}), 1.0)

    def test_validate_receipt_without_picking(self):
        self.assertFalse(self.Wizard._validate_receipt_quantities(False, {}))

    def test_validate_receipt_fallback_partial_quantity(self):
        """Fallback without order context: a partial quantity goes through button_validate."""
        order = self._order([(self.product_a, 5.0), (self.product_b, 1.0)])
        picking = order.picking_ids
        self.assertTrue(self.Wizard._validate_receipt_quantities(picking, {self.product_a.id: 2.0}))
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.move_ids.filtered(lambda move: move.product_id == self.product_a).quantity, 2.0)
        backorder = order.picking_ids - picking
        self.assertEqual(backorder.state, "assigned", "The rest of the receipt goes to a backorder")
        self.assertEqual(
            {(move.product_id, move.product_uom_qty) for move in backorder.move_ids},
            {(self.product_a, 3.0), (self.product_b, 1.0)},
        )

    def test_validate_receipt_fallback_blocked_by_another_wizard(self):
        """A pre-validation wizard returned by button_validate leaves the receipt undone."""
        order = self._order([(self.product_a, 5.0)])
        picking = order.picking_ids
        picking_cls = type(picking)
        with patch.object(picking_cls, "button_validate", return_value={"type": "ir.actions.act_window"}):
            self.assertFalse(self.Wizard._validate_receipt_quantities(picking, {self.product_a.id: 5.0}))
        self.assertNotEqual(picking.state, "done")

    def test_receipt_not_validated_is_reported(self):
        order = self._order([(self.product_a, 5.0)])
        wizard_cls = type(self.Wizard)
        with patch.object(wizard_cls, "_validate_receipt_quantities", return_value=False):
            wizard = self._import(
                order, [{"code": "FLOW-A", "name": self.product_a.name, "qty": "5"}], validate_receipt=True
            )
        self.assertIn("could not be validated", wizard.log)
        self.assertNotIn("Receipt updated", wizard.log)
        self.assertIn("text-warning", wizard.log_html)

    # ------------------------------------------------------------------
    # Vendor bill
    # ------------------------------------------------------------------
    def test_bill_tax_rate_from_xml(self):
        """An 11% line replaces the 21% order tax; a rate without a matching tax keeps it."""
        order = self._order([(self.product_a, 1.0), (self.product_b, 1.0)])
        self._import(
            order,
            [
                {"code": "FLOW-A", "name": self.product_a.name, "qty": "1", "tax": "11", "tax_category": "S"},
                {"code": "FLOW-B", "name": self.product_b.name, "qty": "1", "tax": "7", "tax_category": "S"},
            ],
            invoice_id="FLOW-BILL-1",
        )
        bill = order.invoice_ids
        self.assertEqual(len(bill), 1)
        lines = bill.invoice_line_ids
        self.assertEqual(lines.filtered(lambda line: line.product_id == self.product_a).tax_ids, self.tax_11)
        self.assertEqual(lines.filtered(lambda line: line.product_id == self.product_b).tax_ids, self.tax_21)

    def test_apply_xml_taxes_by_product_fallback(self):
        """Source lines without a purchase line: the rate goes by product when unambiguous."""
        order = self._order([(self.product_a, 1.0), (self.product_b, 1.0)])
        order.action_create_invoice()
        bill = order.invoice_ids
        bill.write({"invoice_line_ids": [(0, 0, {"display_type": "line_note", "name": "Flow note"})]})
        self.Wizard._apply_xml_taxes_to_bill(
            bill,
            [
                {"product": self.product_a, "tax_percent": 11.0},
                {"product": self.product_b, "tax_percent": 11.0},
                {"product": self.product_b, "tax_percent": 21.0},
                {"product": self.product_b, "tax_percent": None},
            ],
        )
        lines = bill.invoice_line_ids.filtered("product_id")
        self.assertEqual(lines.filtered(lambda line: line.product_id == self.product_a).tax_ids, self.tax_11)
        # two different rates for B: left as on the order
        self.assertEqual(lines.filtered(lambda line: line.product_id == self.product_b).tax_ids, self.tax_21)

    def test_source_tax_percent(self):
        self.assertIsNone(self.Wizard._source_tax_percent({}))
        self.assertIsNone(self.Wizard._source_tax_percent({"tax_percent": 0.0, "tax_category": "AE"}))
        self.assertEqual(self.Wizard._source_tax_percent({"tax_percent": 0.0, "tax_category": "e"}), 0.0)
        self.assertEqual(self.Wizard._source_tax_percent({"tax_percent": "11"}), 11.0)

    def test_no_ghost_bill_when_order_already_invoiced(self):
        """A second supplier invoice on a fully invoiced order creates no zero-quantity bill."""
        order = self._order([(self.product_a, 1.0)])
        order.action_create_invoice()
        order.invoice_ids.ref = "FLOW-FIRST"
        wizard = self._import(
            order, [{"code": "FLOW-A", "name": self.product_a.name, "qty": "1"}], invoice_id="FLOW-SECOND"
        )
        self.assertEqual(len(order.invoice_ids), 1)
        self.assertFalse(wizard.bill_id)
        self.assertIn("nothing left to invoice", wizard.log)
        self.assertTrue(wizard.has_warning, "A second invoice on an invoiced order needs a review")

    def test_no_bill_before_receipt_when_billed_on_received_quantities(self):
        product = self.env["product.product"].create(
            {"name": "Flow Receive Policy", "default_code": "FLOW-R", "is_storable": True, "purchase_method": "receive"}
        )
        order = self._order([(product, 2.0)])
        wizard = self._import(order, [{"code": "FLOW-R", "name": product.name, "qty": "2"}], invoice_id="FLOW-R-1")
        self.assertFalse(order.invoice_ids)
        self.assertIn("nothing left to invoice", wizard.log)

    def test_bill_created_after_receipt_when_billed_on_received_quantities(self):
        product = self.env["product.product"].create(
            {
                "name": "Flow Receive Billed",
                "default_code": "FLOW-RB",
                "is_storable": True,
                "purchase_method": "receive",
            }
        )
        order = self._order([(product, 2.0)])
        wizard = self._import(
            order,
            [{"code": "FLOW-RB", "name": product.name, "qty": "2", "line_total": "20"}],
            invoice_id="FLOW-RB-1",
            validate_receipt=True,
        )
        self.assertEqual(order.invoice_ids.invoice_line_ids.quantity, 2.0)
        self.assertEqual(wizard.bill_id, order.invoice_ids)
        self.assertFalse(wizard.has_warning)
