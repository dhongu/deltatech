# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleTransferUom(TransactionCase):
    """SALETRANSFER-001: the transfer demand is computed in one unit (the product unit)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # a dedicated company, so the "other" warehouse found by prepare_transfer is ours
        cls.company = cls.env["res.company"].create({"name": "Sale Transfer UoM Co"})
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[cls.company.id]))
        cls.wh_sale = cls.env["stock.warehouse"].search([("company_id", "=", cls.company.id)], limit=1)
        cls.wh_source = cls.env["stock.warehouse"].create(
            {"name": "Source WH", "code": "SRCU", "company_id": cls.company.id}
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.partner = cls.env["res.partner"].create({"name": "Sale Transfer Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "Sale Transfer Product", "is_storable": True, "uom_id": cls.uom_unit.id}
        )

    def _stock(self, warehouse, qty):
        self.env["stock.quant"]._update_available_quantity(self.product, warehouse.lot_stock_id, qty)

    def _confirm(self, lines):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "warehouse_id": self.wh_sale.id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": qty, "product_uom_id": uom.id})
                    for qty, uom in lines
                ],
            }
        )
        order.with_context(confirm_transfer=False).action_confirm()
        return order

    def _transfer_moves(self, order):
        return self.env["stock.move"].search(
            [
                ("picking_id.origin", "=", order.name),
                ("location_id", "child_of", self.wh_source.view_location_id.id),
            ]
        )

    def test_shortage_in_dozens_is_transferred_in_product_unit(self):
        self._stock(self.wh_sale, 6)
        self._stock(self.wh_source, 100)

        order = self._confirm([(1, self.uom_dozen)])

        moves = self._transfer_moves(order)
        self.assertRecordValues(moves, [{"product_uom": self.uom_unit.id, "product_uom_qty": 6.0}])

    def test_transfer_never_exceeds_source_stock_for_repeated_lines(self):
        self._stock(self.wh_sale, 6)
        self._stock(self.wh_source, 10)

        order = self._confirm([(1, self.uom_dozen), (1, self.uom_dozen)])

        moves = self._transfer_moves(order)
        self.assertTrue(all(move.product_uom == self.uom_unit for move in moves))
        # missing: 24 - 6 = 18 units, but only 10 units are available at the source
        self.assertEqual(sum(moves.mapped("product_uom_qty")), 10.0)
