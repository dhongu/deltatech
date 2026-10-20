# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from base64 import b64encode

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .test_ubl_import import _xml_invoice


@tagged("post_install", "-at_install")
class TestUblImportVatCheck(TransactionCase):
    """The order is compared with the document on the total with VAT too, and a line whose
    VAT differs from the document is reported (only reported: the VAT of the order comes
    from the product and the vendor's fiscal position)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Wizard = cls.env["purchase.ubl.import.wizard"]
        cls.tax_21 = cls.env["account.tax"].create(
            {"name": "VAT Check 21%", "amount": 21.0, "amount_type": "percent", "type_tax_use": "purchase"}
        )
        cls.vendor = cls.env["res.partner"].create(
            {"name": "VAT Check Vendor s.r.o.", "is_company": True, "vat": "CZ27740773", "supplier_rank": 1}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "VAT Check Mats",
                "type": "consu",
                "default_code": "VATCHK-1",
                "supplier_taxes_id": [(6, 0, cls.tax_21.ids)],
            }
        )

    def _import(self, tax="0", tax_category="K", total="25", **xml):
        order = self.env["purchase.order"].create({"partner_id": self.vendor.id, "company_id": self.company.id})
        content = _xml_invoice(
            order_ref="",
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            tax_exclusive_amount="25",
            tax_inclusive_amount=total,
            lines=[
                {
                    "code": "VATCHK-1",
                    "name": "VAT Check Mats",
                    "qty": "2",
                    "price": "12.5",
                    "line_total": "25",
                    "tax": tax,
                    "tax_category": tax_category,
                }
            ],
            **xml,
        )
        wizard = self.Wizard.with_context(active_model="purchase.order", active_id=order.id).create(
            {"data_file": b64encode(content), "create_bill": False}
        )
        wizard.action_import()
        return order, wizard

    def test_intra_community_invoice_on_an_order_with_domestic_vat(self):
        """A 0% intra-community invoice imported on an order whose lines took the domestic 21%:
        the value without VAT matches, the total with VAT and the line VAT do not."""
        order, wizard = self._import()
        self.assertEqual(order.order_line.tax_ids, self.tax_21, "the import does not change the VAT itself")
        self.assertIn("Total check OK: purchase order untaxed total 25.00", wizard.log)
        self.assertIn("purchase order total 30.25", wizard.log)
        self.assertIn("differs from XML total 25.00", wizard.log)
        self.assertIn("VAT rate differs on 1 line(s) (VATCHK-1): the document has 0%, the order 21%", wizard.log)
        self.assertTrue(wizard.has_warning)

    def test_same_vat_on_document_and_order(self):
        order, wizard = self._import(tax="21", tax_category="S", total="30.25")
        self.assertIn("Total check OK: purchase order untaxed total 25.00", wizard.log)
        self.assertIn("Total check OK: purchase order total 30.25", wizard.log)
        self.assertNotIn("VAT rate differs", wizard.log)
        self.assertFalse(wizard.has_warning)

    def test_zero_rate_without_category_is_not_compared(self):
        """Vendor-specific PDF parsers report 0 when they could not read the rate."""
        _order, wizard = self._import(tax="0", tax_category="", total="30.25")
        self.assertNotIn("VAT rate differs", wizard.log)
        mapped = [{"purchase_line": _order.order_line, "tax_percent": 0.0, "code": "VATCHK-1"}]
        self.assertTrue(self.Wizard._tax_check_messages({"tax_percent_read": True}, mapped))

    def _reverse_charge_tax(self):
        return self.tax_21.copy(
            {
                "name": "VAT Check 21% intra-community",
                "invoice_repartition_line_ids": [
                    (5, 0, 0),
                    (0, 0, {"repartition_type": "base"}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": 100}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": -100}),
                ],
                "refund_repartition_line_ids": [
                    (5, 0, 0),
                    (0, 0, {"repartition_type": "base"}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": 100}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": -100}),
                ],
            }
        )

    def test_reverse_charge_tax_counts_as_zero(self):
        """An intra-community tax charges nothing on the order: the buyer collects and deducts
        the same amount, so it matches a 0% intra-community (K) document."""
        self.product.supplier_taxes_id = self._reverse_charge_tax()
        order, wizard = self._import()
        self.assertEqual(order.amount_total, 25.0)
        self.assertNotIn("VAT rate differs", wizard.log)
        self.assertIn("Total check OK: purchase order total 25.00", wizard.log)

    def test_total_with_vat_is_compared_before_any_advance(self):
        """The order total is compared with the invoice total with VAT, not with the amount
        left to pay after an advance already paid."""
        _order, wizard = self._import(tax="21", tax_category="S", total="30.25", payable_amount="10.25")
        self.assertIn("Total check OK: purchase order total 30.25", wizard.log)

    def test_reverse_charge_on_an_exempt_document_is_reported(self):
        """Under an exemption (E), a zero rate, an operation outside the scope of VAT or an
        export the buyer does not self-assess the VAT: a reverse charge tax on the order is
        reported, though it charges nothing either."""
        self.product.supplier_taxes_id = self._reverse_charge_tax()
        _order, wizard = self._import(tax_category="E")
        self.assertIn("the document has 0%, the order 21% reverse charge", wizard.log)
