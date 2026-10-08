# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from base64 import b64encode

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .test_ubl_import import _xml_invoice


@tagged("post_install", "-at_install")
class TestUblImportLineMapping(TransactionCase):
    """UBL-001/002/003: source lines are applied line by line, not per product."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.vendor = cls.env["res.partner"].create(
            {"name": "Lines Vendor SRL", "is_company": True, "vat": "RO99887766", "supplier_rank": 1}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Lines Product", "default_code": "LINEPROD", "is_storable": True, "purchase_ok": True}
        )
        Tax = cls.env["account.tax"]
        tax_vals = {"type_tax_use": "purchase", "amount_type": "percent", "company_id": cls.company.id}
        cls.tax_21 = Tax.create(dict(tax_vals, name="LINES Purchase 21%", amount=21))
        cls.tax_9 = Tax.create(dict(tax_vals, name="LINES Purchase 9%", amount=9))
        cls.tax_0 = Tax.create(dict(tax_vals, name="LINES Purchase 0%", amount=0))

    def _order(self, quantities):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": qty,
                            "price_unit": 10.0,
                            "name": self.product.name,
                            "product_uom_id": self.product.uom_id.id,
                            "date_planned": "2025-01-01 00:00:00",
                            "tax_ids": [(6, 0, self.tax_21.ids)],
                        },
                    )
                    for qty in quantities
                ],
            }
        )
        order.button_confirm()
        return order

    def _import(self, order, lines, create_bill=False, validate_receipt=False, invoice_id="LINES-INV"):
        xml = _xml_invoice(
            invoice_id=invoice_id,
            order_ref=order.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[
                dict({"code": "LINEPROD", "name": self.product.name, "price": "10.0", "unit_code": "C62"}, **line)
                for line in lines
            ],
        )
        wizard = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=order.id)
            .create(
                {
                    "data_file": b64encode(xml),
                    "filename": "lines.xml",
                    "update_prices": False,
                    "create_bill": create_bill,
                    "validate_receipt": validate_receipt,
                    "create_missing_products": False,
                }
            )
        )
        wizard.action_import()
        return wizard

    def _bill_rates(self, order):
        bill = order.invoice_ids
        self.assertEqual(len(bill), 1)
        return [sum(line.tax_ids.mapped("amount")) for line in bill.invoice_line_ids.sorted("quantity")]

    def test_explicit_zero_rate_is_applied(self):
        """UBL-001: Percent 0 with category Z replaces the 21% default tax"""
        order = self._order([3.0])
        self._import(order, [{"qty": "3", "line_total": "30", "tax": "0", "tax_category": "Z"}], create_bill=True)
        self.assertEqual(self._bill_rates(order), [0.0])

    def test_zero_rate_not_vat_registered_supplier(self):
        """Category O (supplier not registered for VAT) does not keep a 21% tax"""
        order = self._order([3.0])
        self._import(order, [{"qty": "3", "line_total": "30", "tax": "0", "tax_category": "O"}], create_bill=True)
        self.assertEqual(self._bill_rates(order), [0.0])

    def test_zero_rate_reverse_charge_keeps_tax(self):
        """A 0 rate with reverse charge (AE) keeps the buyer tax of the order"""
        order = self._order([3.0])
        self._import(order, [{"qty": "3", "line_total": "30", "tax": "0", "tax_category": "AE"}], create_bill=True)
        self.assertEqual(order.invoice_ids.invoice_line_ids.tax_ids, self.tax_21)

    def test_same_product_with_different_rates(self):
        """UBL-002: two lines of the same product keep their own rate"""
        order = self._order([2.0, 3.0])
        self._import(
            order,
            [
                {"qty": "2", "line_total": "20", "tax": "21", "tax_category": "S"},
                {"qty": "3", "line_total": "30", "tax": "9", "tax_category": "S"},
            ],
            create_bill=True,
        )
        self.assertEqual(self._bill_rates(order), [21.0, 9.0])

    def test_repeated_product_receipt_total(self):
        """UBL-003: 2 + 3 units of the same product are received as 5, not 3 per move"""
        order = self._order([5.0])
        picking = order.picking_ids
        self._import(
            order,
            [{"qty": "2", "line_total": "20", "tax": "21"}, {"qty": "3", "line_total": "30", "tax": "21"}],
            validate_receipt=True,
        )
        self.assertEqual(picking.state, "done")
        received = sum(order.picking_ids.filtered(lambda p: p.state == "done").move_ids.mapped("quantity"))
        self.assertEqual(received, 5.0)
        self.assertEqual(sum(order.order_line.mapped("qty_received")), 5.0)
