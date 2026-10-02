# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestForcePriceAtValidation(TransactionCase):
    """PURCHASEPRICE-002: forced supplier prices use product_uom_id (Odoo 19)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.currency = cls.env.company.currency_id
        cls.vendor = cls.env["res.partner"].create({"name": "Force price vendor"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Force price product",
                "type": "consu",
                "uom_id": cls.uom_unit.id,
                "standard_price": 10,
                "seller_ids": [
                    (0, 0, {"partner_id": cls.vendor.id, "price": 10, "currency_id": cls.currency.id}),
                ],
            }
        )
        cls.seller = cls.product.seller_ids
        cls.env["ir.config_parameter"].sudo().set_param("purchase.force_price_at_validation", "True")

    def _confirm_po(self, price_unit, uom):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "currency_id": self.currency.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1,
                            "product_uom_id": uom.id,
                            "price_unit": price_unit,
                        },
                    )
                ],
            }
        )
        order.order_line.price_unit = price_unit
        order.button_confirm()
        return order

    def test_po_confirmation_same_unit(self):
        order = self._confirm_po(12, self.uom_unit)
        self.assertEqual(order.state, "purchase")
        self.assertAlmostEqual(self.seller.price, 12)

    def test_po_confirmation_different_unit(self):
        order = self._confirm_po(240, self.uom_dozen)
        self.assertEqual(order.state, "purchase")
        # 240 per dozen = 20 per unit, the unit of the supplier row
        self.assertAlmostEqual(self.seller.price, 20)

    def test_po_confirmation_supplier_row_in_dozens(self):
        self.seller.product_uom_id = self.uom_dozen
        self._confirm_po(15, self.uom_unit)
        # 15 per unit = 180 per dozen, the unit of the supplier row
        self.assertAlmostEqual(self.seller.price, 180)

    def test_po_confirmation_force_disabled(self):
        self.env["ir.config_parameter"].sudo().set_param("purchase.force_price_at_validation", "False")
        self._confirm_po(240, self.uom_dozen)
        self.assertAlmostEqual(self.seller.price, 10)

    def test_bill_posting_different_unit(self):
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.vendor.id,
                "invoice_date": fields.Date.today(),
                "currency_id": self.currency.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "product_uom_id": self.uom_dozen.id,
                            "price_unit": 360,
                        },
                    )
                ],
            }
        )
        bill.invoice_line_ids.write({"product_uom_id": self.uom_dozen.id, "price_unit": 360})
        bill.action_post()
        self.assertEqual(bill.state, "posted")
        self.assertAlmostEqual(self.seller.price, 30)
