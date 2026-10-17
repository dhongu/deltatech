# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Issue #3458: the cost from the deliveries adds quantities in different units.

from odoo.tests import tagged

from .test_sale import TestSaleCommissionBase


@tagged("post_install", "-at_install")
class TestPurchasePriceUom(TestSaleCommissionBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unit = cls.env.ref("uom.product_uom_unit")
        cls.dozen = cls.env.ref("uom.product_uom_dozen")

    def _deliver_mixed_units(self, sale_uom, sale_qty):
        """Sell 24 pieces, delivered as 12 pieces + 1 dozen, each move worth 1200 (100 / piece)."""
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [
                    (
                        0,
                        0,
                        {"product_id": self.product_a.id, "product_uom_id": sale_uom.id, "product_uom_qty": sale_qty},
                    )
                ],
            }
        )
        so.action_confirm()
        sale_line = so.order_line
        picking = so.picking_ids
        move = picking.move_ids
        move.write({"product_uom_qty": 12, "product_uom": self.unit.id})
        move.copy({"picking_id": picking.id, "product_uom_qty": 1, "product_uom": self.dozen.id})
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.move_ids.picked = True
        picking._action_done()
        moves = picking.move_ids.filtered(lambda m: m.state == "done")
        self.assertEqual(moves.sale_line_id, sale_line)
        self.assertEqual(moves.product_uom, self.unit | self.dozen)
        moves.write({"value": 1200})
        return so

    def test_invoice_in_pieces(self):
        so = self._deliver_mixed_units(self.unit, 24)
        invoice = self._create_invoice(so)
        line = invoice.invoice_line_ids
        self.assertEqual(line.product_uom_id, self.unit)
        self.assertAlmostEqual(line.get_purchase_price(), 100)
        self.assertAlmostEqual(line.purchase_price * line.quantity, 2400)

    def test_invoice_in_dozens(self):
        so = self._deliver_mixed_units(self.dozen, 2)
        invoice = self._create_invoice(so)
        line = invoice.invoice_line_ids
        self.assertEqual(line.product_uom_id, self.dozen)
        self.assertAlmostEqual(line.get_purchase_price(), 1200)
        self.assertAlmostEqual(line.purchase_price * line.quantity, 2400)
