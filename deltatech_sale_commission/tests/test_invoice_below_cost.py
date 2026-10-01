# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInvoiceBelowCost(AccountTestInvoicingCommon):
    """The below-cost check of the invoice line in "block" mode.

    The invoice of a confirmed order is issued at the price accepted on the
    order: it must not be refused to whoever issues it. A price set or changed
    on the invoice itself is still checked.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")
        cls.env.company.sale_margin_check_mode = "block"
        cls.product_a.standard_price = 800.0

    def _confirmed_order_below_cost(self):
        # lines passed inline to `create` are not checked by deltatech_sale_margin
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [
                    (0, 0, {"product_id": self.product_a.id, "product_uom_qty": 1, "price_unit": 100.0}),
                ],
            }
        )
        order.action_confirm()
        return order

    def test_user_is_outside_the_bypass_group(self):
        """Guard for the tests themselves: with the bypass group nothing is blocked."""
        self.assertFalse(self.env.user.has_group("deltatech_sale_margin.group_sale_below_purchase_price"))

    def test_invoice_of_confirmed_order_at_order_price(self):
        order = self._confirmed_order_below_cost()
        invoice = order._create_invoices()
        self.assertEqual(invoice.invoice_line_ids.price_unit, 100.0)
        self.assertEqual(invoice.state, "draft")

    def test_price_changed_on_invoice_is_checked(self):
        invoice = self._confirmed_order_below_cost()._create_invoices()
        line = invoice.invoice_line_ids
        # without a delivery the cost of a line from an order is taken from its moves;
        # set it, the line is still at the order price and goes through
        line.purchase_price = 800.0
        with self.assertRaises(UserError):
            line.price_unit = 90.0

    def test_manual_invoice_below_cost_is_blocked(self):
        invoice = self.init_invoice("out_invoice", products=self.product_a)
        with self.assertRaises(UserError):
            invoice.invoice_line_ids.price_unit = 100.0
