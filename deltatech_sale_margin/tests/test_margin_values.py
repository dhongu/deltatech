# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Explicit margin figures. The values asserted here are the ones produced by the
# 19.0 version of the module (and of `sale_margin` / `sale_stock_margin`) for the
# same data: a migration that changes any of them is a regression, not a detail.

from odoo.tests import TransactionCase, tagged

from odoo.addons.stock_account.tests.common import TestStockValuationCommon


@tagged("post_install", "-at_install")
class TestMarginValues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.sale_margin_check_mode = "warn"
        icp = cls.env["ir.config_parameter"].sudo()
        icp.set_float("sale.margin_limit", 0.0)
        icp.set_bool("sale.margin_limit_check_validate", False)
        cls.partner = cls.env["res.partner"].create({"name": "Margin values customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Margin values product",
                "type": "consu",
                "standard_price": 50.0,
                "taxes_id": False,
            }
        )
        cls.tax_included = cls.env["account.tax"].create(
            {
                "name": "VAT 21% included (test)",
                "amount": 21.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "price_include_override": "tax_included",
                "company_id": cls.company.id,
            }
        )
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Margin values operator",
                "login": "margin_values_operator",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("sales_team.group_sale_salesman").id,
                        ],
                    )
                ],
            }
        )

    def _order(self, price, qty=3.0, discount=0.0, taxes=None):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "price_unit": price,
                            "discount": discount,
                            "tax_ids": [(6, 0, (taxes or self.env["account.tax"]).ids)],
                        },
                    )
                ],
            }
        )
        return order, order.order_line

    def test_margin_plain(self):
        order, line = self._order(80.0)
        self.assertRecordValues(
            line,
            [
                {
                    "purchase_price": 50.0,
                    "price_reduce_taxexcl": 80.0,
                    "price_subtotal": 240.0,
                    "margin": 90.0,
                    "margin_percent": 0.375,
                    "margin_below_limit": False,
                }
            ],
        )
        self.assertAlmostEqual(line._margin_for_check(), 37.5, places=6)
        self.assertAlmostEqual(order.margin, 90.0, places=2)
        self.assertAlmostEqual(order.margin_percent, 0.375, places=6)

    def test_margin_with_discount(self):
        order, line = self._order(80.0, discount=10.0)
        # 80 - 10% = 72 per unit; (72 - 50) / 72
        self.assertAlmostEqual(line.price_reduce_taxexcl, 72.0, places=2)
        self.assertAlmostEqual(line.margin, 66.0, places=2)
        self.assertAlmostEqual(line.margin_percent, 0.3056, places=4)
        self.assertAlmostEqual(line._margin_for_check(), 30.555556, places=5)
        self.assertFalse(line.margin_below_limit)
        self.assertAlmostEqual(order.margin, 66.0, places=2)

    def test_margin_with_tax_included_price(self):
        """The check compares the price WITHOUT tax: 121 incl. 21% is 100 net."""
        order, line = self._order(121.0, qty=2.0, taxes=self.tax_included)
        self.assertAlmostEqual(line.price_reduce_taxexcl, 100.0, places=2)
        self.assertAlmostEqual(line.price_subtotal, 200.0, places=2)
        self.assertAlmostEqual(line.margin, 100.0, places=2)
        self.assertAlmostEqual(line.margin_percent, 0.5, places=4)
        self.assertAlmostEqual(line._margin_for_check(), 50.0, places=6)
        self.assertFalse(line.margin_below_limit)

    def test_below_cost_values_and_chatter_note(self):
        order, line = self._order(40.0)
        self.assertAlmostEqual(line.margin, -30.0, places=2)
        self.assertAlmostEqual(line.margin_percent, -0.25, places=4)
        self.assertAlmostEqual(line._margin_for_check(), -25.0, places=6)
        self.assertTrue(line.margin_below_limit)
        order.action_confirm()
        notes = [b for b in order.message_ids.mapped("body") if b and "below cost" in b.lower()]
        self.assertEqual(len(notes), 1)
        self.assertIn("margin -25.0%", notes[0])
        self.assertIn("unit price 40.0", notes[0])

    def test_margin_limit_boundary(self):
        """`margin < limit`, strictly: exactly on the limit is not flagged."""
        self.env["ir.config_parameter"].sudo().set_float("sale.margin_limit", 37.5)
        _, on_limit = self._order(80.0)
        self.assertFalse(on_limit.margin_below_limit)
        _, under = self._order(79.99)
        self.assertTrue(under.margin_below_limit)

    def _margin_lines(self, order):
        return [
            line
            for group in order.extra_total_fields or []
            for line in group.get("lines", [])
            if line.get("value") == order.margin
        ]

    def test_order_margin_total_visible_with_group(self):
        """Admin is in `group_sale_margin`: the order margin line stays in the totals."""
        order, _line = self._order(80.0)
        self.assertTrue(self.env.user.has_group("deltatech_sale_margin.group_sale_margin"))
        margin_lines = self._margin_lines(order)
        self.assertEqual(len(margin_lines), 1)
        self.assertAlmostEqual(margin_lines[0]["value"], 90.0, places=2)
        self.assertIn("38%", margin_lines[0]["label"])

    def test_order_margin_total_hidden_without_group(self):
        """19.0 restricted the order margin block to `group_sale_margin`; in 20.0 it is a
        line of `extra_total_fields` and must stay hidden from the other users."""
        order, _line = self._order(80.0)
        self.assertFalse(self.operator.has_group("deltatech_sale_margin.group_sale_margin"))
        order_as_operator = order.with_user(self.operator)
        self.assertFalse(self._margin_lines(order_as_operator))
        # the margin itself is unchanged - only its display in the totals is hidden
        self.assertAlmostEqual(order_as_operator.margin, 90.0, places=2)


@tagged("post_install", "-at_install")
class TestMarginValuesFromDelivery(TestStockValuationCommon):
    """The cost used by the check is the one `sale_stock_margin` takes from the
    valuation of the delivery (`stock.move.value`, negative on outgoing moves in
    20.0). Same figures as the core `test_sale_stock_margin_2`, in 19.0 and 20.0."""

    _test_user_groups = (
        "sales_team.group_sale_salesman",
        "stock.group_stock_manager",
        "product.group_product_manager",
        "account.group_account_invoice",
        "account.group_account_readonly",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.sale_margin_check_mode = "warn"
        icp = cls.env["ir.config_parameter"].sudo()
        icp.set_float("sale.margin_limit", 0.0)
        icp.set_bool("sale.margin_limit_check_validate", False)
        cls.customer = cls.env["res.partner"].create({"name": "Delivery margin customer"})
        cls.pricelist = cls.env["product.pricelist"].create({"name": "Simple Pricelist", "company_id": False})

    def _fifo_product(self):
        product = self.env["product.product"].create(
            {
                "name": "FIFO margin product",
                "is_storable": True,
                "categ_id": self.env.ref("product.product_category_goods").id,
            }
        )
        product.categ_id.property_cost_method = "fifo"
        return product

    def _sell_and_deliver(self, product, qty, price):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": qty,
                "price_unit": price,
            }
        )
        order.action_confirm()
        before = (line.purchase_price, line.margin_below_limit)
        order.picking_ids.move_ids.write({"quantity": qty, "picked": True})
        order.picking_ids.button_validate()
        return order, line, before

    def test_cost_from_delivery_valuation(self):
        product = self._fifo_product()
        self._make_in_move(product, 2, 32)
        self._make_in_move(product, 5, 17)
        self._make_out_move(product, 1)
        order, line, (cost_before, flag_before) = self._sell_and_deliver(product, 2, 50)
        self.assertAlmostEqual(cost_before, 19.5, places=2)
        self.assertFalse(flag_before)
        self.assertAlmostEqual(line.purchase_price, 24.5, places=2)
        self.assertAlmostEqual(line.margin, 51.0, places=2)
        self.assertAlmostEqual(order.margin, 51.0, places=2)
        self.assertAlmostEqual(line._margin_for_check(), 51.0, places=6)
        self.assertFalse(line.margin_below_limit)

    def test_delivery_cost_turns_line_below_cost(self):
        """Sold at 22: above the standard price (19.5) at confirmation, below the
        real FIFO cost of the delivered units (24.5) once the delivery is done."""
        product = self._fifo_product()
        self._make_in_move(product, 2, 32)
        self._make_in_move(product, 5, 17)
        self._make_out_move(product, 1)
        _order, line, (cost_before, flag_before) = self._sell_and_deliver(product, 2, 22)
        self.assertAlmostEqual(cost_before, 19.5, places=2)
        self.assertFalse(flag_before)
        self.assertAlmostEqual(line.purchase_price, 24.5, places=2)
        self.assertAlmostEqual(line.margin, -5.0, places=2)
        self.assertAlmostEqual(line._margin_for_check(), (22 - 24.5) / 22 * 100, places=6)
        self.assertTrue(line.margin_below_limit)
