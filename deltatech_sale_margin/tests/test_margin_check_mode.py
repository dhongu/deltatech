# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMarginCheckMode(TransactionCase):
    """`res.company.sale_margin_check_mode` decides HOW the system reacts when a
    line falls below cost: block it (historical behaviour, still the default),
    only flag it, or ignore it.

    "Warn only" exists for businesses where selling below cost is routine -
    perishable goods, stock clearance, commercial gestures. There, blocking stops
    the day-to-day work, while the actual need is to see it and decide.

    Every test runs as an OPERATOR who is outside the bypass groups. Running as
    root or admin would prove nothing: both belong to
    `group_sale_below_purchase_price`, so the native check would not have blocked
    them either and the tests would pass with the feature removed.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.config.settings"].create({"group_uom": True}).execute()
        cls.env.user.group_ids |= cls.env.ref("uom.group_uom")
        cls.company = cls.env.company
        cls.env["ir.config_parameter"].sudo().set_param("sale.margin_limit", "0")
        cls.env["ir.config_parameter"].sudo().set_param("sale.margin_limit_check_validate", "0")

        cls.below_cost_group = cls.env.ref("deltatech_sale_margin.group_sale_below_purchase_price")
        cls.below_margin_group = cls.env.ref("deltatech_sale_margin.group_sale_below_margin")
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Sales operator",
                "login": "margin_mode_operator",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("sales_team.group_sale_salesman").id,
                            cls.env.ref("account.group_account_invoice").id,
                        ],
                    )
                ],
            }
        )

        cls.partner = cls.env["res.partner"].create({"name": "Margin mode customer"})
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        # a packaging unit on top of kg, the way goods sold by the box are set up
        cls.uom_box12 = cls.env["uom.uom"].create(
            {
                "name": "Box 12 kg (test)",
                "relative_factor": 12.0,
                "relative_uom_id": cls.uom_kg.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Margin mode product",
                "type": "consu",
                "uom_id": cls.uom_kg.id,
                "standard_price": 3.0,  # 3/kg -> 36/Box 12 kg
                "taxes_id": False,
            }
        )

    def _order(self, price, uom=None, qty=100.0, product=None, user=None):
        env = self.env(user=user) if user else self.env
        order = env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": (product or self.product).id,
                            "product_uom_qty": qty,
                            "product_uom_id": (uom or self.uom_kg).id,
                            "price_unit": price,
                            "tax_ids": [(5, 0, 0)],
                        },
                    )
                ],
            }
        )
        return order, order.order_line

    # ------------------------------------------------------------------ guards

    def test_operator_is_outside_the_bypass_groups(self):
        """Guard for the tests themselves - see the class docstring."""
        self.assertNotIn(self.below_cost_group, self.operator.group_ids)
        self.assertNotIn(self.below_margin_group, self.operator.group_ids)
        self.assertFalse(self.operator.has_group("deltatech_sale_margin.group_sale_below_purchase_price"))

    def test_default_mode_is_block(self):
        """Existing databases must not change behaviour on upgrade."""
        self.assertEqual(
            self.env["res.company"].create({"name": "Fresh company"}).sale_margin_check_mode,
            "block",
        )

    # ------------------------------------------------------------------- block

    def test_block_mode_still_blocks(self):
        """The historical reaction is unchanged for everybody who does not opt out.

        The block lands on `write` and on confirmation, not on `create`: with the
        order lines passed inline, `create` never goes through
        `sale.order.line.write`. That is pre-existing behaviour, asserted here so
        a future change to it does not pass unnoticed.
        """
        self.company.sale_margin_check_mode = "block"
        order, line = self._order(2.5, user=self.operator)
        with self.assertRaises(UserError):
            line.write({"price_unit": 2.4})

    def test_block_mode_blocks_on_confirmation_when_configured(self):
        """With "check on confirmation only", the block lands in `action_confirm`.

        Without that parameter the block only ever fires from
        `sale.order.line.write`: confirming an order does not itself write on the
        lines, so a below-cost order created through the API and confirmed without
        touching a line goes through even in "block" mode. That is pre-existing
        behaviour - asserted here so the two code paths stay distinguishable.
        """
        self.company.sale_margin_check_mode = "block"
        self.env["ir.config_parameter"].sudo().set_param("sale.margin_limit_check_validate", "1")
        order, _line = self._order(2.5, user=self.operator)
        with self.assertRaises(UserError):
            order.action_confirm()

    # -------------------------------------------------------------------- warn

    def test_warn_mode_flags_without_blocking(self):
        self.company.sale_margin_check_mode = "warn"
        order, line = self._order(2.5, user=self.operator)
        self.assertTrue(line.margin_below_limit)
        self.assertIn("lower than the purchase price", order.price_warning_message)
        self.assertIn("can still be confirmed", order.price_warning_message)

    def test_warn_mode_allows_confirmation_and_logs_it_once(self):
        self.company.sale_margin_check_mode = "warn"
        order, line = self._order(2.5, user=self.operator)
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        notes = [b for b in order.message_ids.mapped("body") if b and "below cost" in b.lower()]
        self.assertEqual(len(notes), 1, "the decision is logged exactly once")

    def test_warn_mode_allows_editing_the_price(self):
        """`check_sale_price` runs on every `write` of a line, so a blocking
        reaction there stops the seller from simply correcting a price."""
        self.company.sale_margin_check_mode = "warn"
        order, line = self._order(4.0, user=self.operator)
        line.write({"price_unit": 1.0})
        self.assertTrue(line.margin_below_limit)

    def test_warn_mode_does_not_flood_the_chatter(self):
        """Repeated price edits must not each leave a message.

        The native code posted from `check_sale_price` for users in the bypass
        group, which produced one chatter entry per keystroke on the price.
        """
        self.company.sale_margin_check_mode = "warn"
        order, line = self._order(2.5, user=self.operator)
        before = len(order.message_ids)
        for price in (2.4, 2.3, 2.2):
            line.write({"price_unit": price})
        self.assertEqual(len(order.message_ids), before)

    def test_warn_mode_allows_invoicing(self):
        """The invoice-side constraint lives in `deltatech_sale_commission`; if it
        ignored the mode, the wall would come at invoicing, once the goods are
        already delivered."""
        if "purchase_price" not in self.env["account.move.line"]._fields:
            self.skipTest("deltatech_sale_commission is not installed")
        self.company.sale_margin_check_mode = "warn"
        order, line = self._order(2.5, user=self.operator)
        order.action_confirm()
        line.qty_delivered = line.product_uom_qty
        invoice = order._create_invoices()
        self.assertEqual(invoice.state, "draft")

    def test_warn_mode_suppresses_the_onchange_modal(self):
        """In "warn" mode the signal is the flagged row, not a modal to dismiss."""
        self.company.sale_margin_check_mode = "warn"
        _, line = self._order(2.5)
        self.assertNotIn("warning", line.price_unit_change() or {})

    def test_block_mode_keeps_the_onchange_modal(self):
        self.company.sale_margin_check_mode = "block"
        new_line = self.env["sale.order.line"].new(
            {
                "order_id": self._order(10.0)[0].id,
                "product_id": self.product.id,
                "product_uom_qty": 1.0,
                "price_unit": 1.0,
            }
        )
        self.assertIn("warning", new_line.price_unit_change() or {})

    # --------------------------------------------------------------------- off

    def test_off_mode_is_silent(self):
        self.company.sale_margin_check_mode = "off"
        order, line = self._order(2.5, user=self.operator)
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertFalse(line.margin_below_limit)
        self.assertFalse(order.price_warning_message)

    # ------------------------------------------------------------------- limit

    def test_negative_limit_tolerates_small_losses(self):
        """A margin that is legitimately negative should not raise a flag on half
        the orders, or nobody reads the flag any more."""
        self.company.sale_margin_check_mode = "warn"
        self.env["ir.config_parameter"].sudo().set_param("sale.margin_limit", "-10")
        _, small_loss = self._order(2.86)  # about -4.9% against 3.00
        self.assertFalse(small_loss.margin_below_limit)
        _, big_loss = self._order(2.4)  # -25%
        self.assertTrue(big_loss.margin_below_limit)

    def test_positive_limit_flags_thin_margins(self):
        self.company.sale_margin_check_mode = "warn"
        self.env["ir.config_parameter"].sudo().set_param("sale.margin_limit", "20")
        _, thin = self._order(3.34)  # about 10.2%
        self.assertTrue(thin.margin_below_limit)
        _, healthy = self._order(5.0)  # 40%
        self.assertFalse(healthy.margin_below_limit)

    # -------------------------------------------------------------------- units

    def test_cost_is_compared_in_the_line_unit(self):
        """Sold by the box while the cost is per kg: the comparison uses the
        CONVERTED cost (36/box), not the raw 3/kg."""
        self.company.sale_margin_check_mode = "warn"
        _, above = self._order(40.0, uom=self.uom_box12, qty=10.0)
        self.assertAlmostEqual(above.purchase_price, 36.0, places=2)
        self.assertFalse(above.margin_below_limit)
        _, below = self._order(30.0, uom=self.uom_box12, qty=10.0)
        self.assertTrue(
            below.margin_below_limit,
            "30 per box is below the converted cost of 36 - comparing 30 against "
            "3 per kg would look like a 90% margin and miss it silently",
        )

    def test_incompatible_unit_families_stay_silent(self):
        """A product whose `uom_id` is wrong must not flag every single line.

        Odoo 19 converts any pair of units by their absolute factors, without
        checking the family: the unit category is gone and the root of the
        kilogram hierarchy is the gram, so a cost of 3.00 per Unit becomes 3000.00
        per kg. Unchecked, that marks everything as below cost and the flag is
        dismissed as noise from day one.

        The opposite direction (`uom_id`=kg, line in Units) is useless as a test:
        the conversion yields 0.003, the margin looks huge and no flag is raised
        either way.
        """
        self.company.sale_margin_check_mode = "warn"
        wrong_uom_product = self.env["product.product"].create(
            {
                "name": "Product with a wrong uom_id",
                "type": "consu",
                "uom_id": self.uom_unit.id,  # wrong: should be kg
                "standard_price": 3.0,
                "taxes_id": False,
            }
        )
        order, line = self._order(50.0, uom=self.uom_kg, qty=10.0, product=wrong_uom_product)
        # the native conversion does inflate the cost 1000x - this is what the
        # guard protects against, asserted rather than assumed
        self.assertAlmostEqual(line.purchase_price, 3000.0, places=2)
        self.assertFalse(line.margin_below_limit)
        self.assertFalse(order.price_warning_message)

    def test_no_cost_no_flag(self):
        """Purchase price never filled in: nothing to compare, so no flag."""
        self.company.sale_margin_check_mode = "warn"
        no_cost = self.env["product.product"].create(
            {
                "name": "Product without a cost",
                "type": "consu",
                "uom_id": self.uom_kg.id,
                "standard_price": 0.0,
                "taxes_id": False,
            }
        )
        order, line = self._order(4.0, product=no_cost)
        self.assertFalse(line.margin_below_limit)
        self.assertFalse(order.price_warning_message)

    def test_flag_is_readable_without_cost_rights(self):
        """The flag must be readable by sellers who cannot see the cost - they are
        exactly the people the warning is for. The figure stays on the native
        `margin_percent`, which is group-restricted."""
        self.company.sale_margin_check_mode = "warn"
        _, line = self._order(2.5, user=self.operator)
        self.assertTrue(line.margin_below_limit)
