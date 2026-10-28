# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleMarginReport(AccountTestInvoicingCommon):
    """The margin report without the commissions: invoice lines, cost and rights."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")
        cls.product = cls.env["product.product"].create({"name": "Margin", "standard_price": 60, "list_price": 100})
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_line_ids": [(0, 0, {"product_id": cls.product.id, "quantity": 3, "price_unit": 100})],
            }
        )
        cls.invoice.action_post()
        cls.env.flush_all()

    def _row(self):
        return self.env["sale.margin.report"].search([("invoice_id", "=", self.invoice.id)])

    def test_invoice_line_in_report(self):
        row = self._row()
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.sale_val, 300)
        self.assertAlmostEqual(row.stock_val, 180)
        self.assertAlmostEqual(row.profit_val, 120)
        self.assertEqual(row.user_id, self.invoice.invoice_user_id)

    def test_manager_changes_cost(self):
        row = self._row()
        row.write({"purchase_price": 50})
        self.assertAlmostEqual(self.invoice.invoice_line_ids.purchase_price, 50)
        self.assertAlmostEqual(row.stock_val, 150)

    def test_line_in_other_unit(self):
        """A line sold by the dozen: quantity and cost per product unit, the value unchanged."""
        dozen = self.env.ref("uom.product_uom_dozen")
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": self.product.id, "quantity": 2, "product_uom_id": dozen.id, "price_unit": 1200},
                    )
                ],
            }
        )
        invoice.action_post()
        self.env.flush_all()
        line = invoice.invoice_line_ids
        self.assertAlmostEqual(line.purchase_price, 720)
        row = self.env["sale.margin.report"].search([("invoice_id", "=", invoice.id)])
        self.assertEqual(row.product_uom, self.product.uom_id)
        self.assertAlmostEqual(row.product_uom_qty, 24)
        self.assertAlmostEqual(row.purchase_price, 60)
        self.assertAlmostEqual(row.stock_val, 1440)
        self.assertAlmostEqual(row.profit_val, 960)
        row.write({"purchase_price": 50})
        self.assertAlmostEqual(line.purchase_price, 600)
        self.assertAlmostEqual(row.stock_val, 1200)

    def test_storable_filter(self):
        storable = self.env["product.product"].create(
            {"name": "Storable", "is_storable": True, "standard_price": 10, "list_price": 20}
        )
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_line_ids": [(0, 0, {"product_id": storable.id, "quantity": 1, "price_unit": 20})],
            }
        )
        invoice.action_post()
        self.env.flush_all()
        rows = self.env["sale.margin.report"].search(
            [("invoice_id", "in", (self.invoice | invoice).ids), ("is_storable", "=", True)]
        )
        self.assertEqual(rows.product_id, storable)

    def test_salesman_can_not_read(self):
        salesman = self.env["res.users"].create(
            {
                "name": "Salesman",
                "login": "margin_salesman",
                "group_ids": [(6, 0, [self.env.ref("sales_team.group_sale_salesman").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.env["sale.margin.report"].with_user(salesman).search([])
