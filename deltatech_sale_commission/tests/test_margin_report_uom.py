# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# COMMISSION-001: the margin report converts the invoice quantity to the product unit.

from odoo.tests import tagged

from .test_sale import TestSaleCommissionBase


@tagged("post_install", "-at_install")
class TestMarginReportUom(TestSaleCommissionBase):
    def _post_move(self, move_type, uom, quantity):
        move = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "product_uom_id": uom.id,
                            "quantity": quantity,
                            "price_unit": 5000,
                        },
                    )
                ],
            }
        )
        move.action_post()
        self.env.flush_all()
        return self.env["sale.margin.report"].search([("invoice_id", "=", move.id)])

    def test_invoice_quantity_in_product_unit(self):
        dozen = self.env.ref("uom.product_uom_dozen")
        unit = self.product_a.uom_id
        self.assertEqual(unit, self.env.ref("uom.product_uom_unit"))
        expected = dozen._compute_quantity(2, unit)
        self.assertEqual(expected, 24)

        line = self._post_move("out_invoice", dozen, 2)
        self.assertEqual(line.product_uom, unit)
        self.assertAlmostEqual(line.product_uom_qty, expected)

        refund = self._post_move("out_refund", dozen, 2)
        self.assertAlmostEqual(refund.product_uom_qty, -expected)

    def test_quantity_in_product_unit_unchanged(self):
        line = self._post_move("out_invoice", self.product_a.uom_id, 7)
        self.assertAlmostEqual(line.product_uom_qty, 7)
