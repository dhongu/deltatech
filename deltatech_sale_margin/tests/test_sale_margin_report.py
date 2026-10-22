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
