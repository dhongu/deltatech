# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNoChangePrice(TransactionCase):
    """`group_sale_no_change_price` is enforced on the server, not only by the
    readonly price/discount in the form (MARGIN-002, issue #3462).

    The margin check is turned off so that every block below comes from the
    price-change restriction and not from the below-cost policy.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.sale_margin_check_mode = "off"
        base_groups = [
            cls.env.ref("base.group_user").id,
            cls.env.ref("sales_team.group_sale_salesman").id,
        ]
        cls.restricted = cls.env["res.users"].create(
            {
                "name": "No price change seller",
                "login": "no_change_price_seller",
                "group_ids": [
                    (6, 0, base_groups + [cls.env.ref("deltatech_sale_margin.group_sale_no_change_price").id])
                ],
            }
        )
        cls.seller = cls.env["res.users"].create(
            {
                "name": "Ordinary seller",
                "login": "price_change_seller",
                "group_ids": [(6, 0, base_groups)],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "No change price customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "No change price product",
                "type": "consu",
                "list_price": 100.0,
                "standard_price": 50.0,
                "taxes_id": False,
            }
        )

    def _order(self, user, line_vals=None):
        vals = {"product_id": self.product.id, "product_uom_qty": 1.0, "tax_ids": [(5, 0, 0)]}
        vals.update(line_vals or {})
        order = (
            self.env["sale.order"].with_user(user).create({"partner_id": self.partner.id, "order_line": [(0, 0, vals)]})
        )
        return order, order.order_line

    def test_restricted_user_cannot_write_price(self):
        order, line = self._order(self.restricted)
        self.assertEqual(line.price_unit, 100.0)
        with self.assertRaises(AccessError):
            line.write({"price_unit": 120.0})

    def test_restricted_user_cannot_write_discount(self):
        order, line = self._order(self.restricted)
        with self.assertRaises(AccessError):
            line.write({"discount": 10.0})

    def test_restricted_user_cannot_change_price_through_the_order(self):
        order, line = self._order(self.restricted)
        with self.assertRaises(AccessError):
            order.write({"order_line": [(1, line.id, {"price_unit": 120.0})]})

    def test_restricted_user_can_work_with_pricelist_price(self):
        """Same values as the pricelist, quantity changes: nothing is blocked."""
        order, line = self._order(self.restricted)
        line.write({"price_unit": 100.0, "discount": 0.0, "product_uom_qty": 3.0})
        self.assertEqual(line.price_unit, 100.0)
        self.assertEqual(order.amount_untaxed, 300.0)

    def test_restricted_user_can_write_the_computed_price(self):
        """A module writing the value the pricelist computes, outside of a compute
        (sale_edi_ubl, deltatech_discount_policy), is not a manual change."""
        order, line = self._order(self.restricted)
        self.product.list_price = 110.0
        line.write({"price_unit": 110.0})
        self.assertEqual(line.price_unit, 110.0)

    def test_direct_price_computation_is_allowed(self):
        """repair / sale_management call `_compute_price_unit()` directly: the
        values are written with `sale_write_from_compute`."""
        order, line = self._order(self.restricted)
        self.product.list_price = 110.0
        line.with_context(force_price_recomputation=True)._compute_price_unit()
        self.assertEqual(line.price_unit, 110.0)

    def test_server_flows_creating_priced_lines_are_allowed(self):
        """RMA handling fee / replacement order, EDI, EDInet and Excel imports
        create lines with their own price under the current user."""
        order, line = self._order(self.restricted, {"price_unit": 0.0})
        self.assertEqual(line.price_unit, 0.0)
        fee = (
            self.env["sale.order.line"]
            .with_user(self.restricted)
            .create({"order_id": order.id, "product_id": self.product.id, "product_uom_qty": 1.0, "price_unit": 15.0})
        )
        self.assertEqual(fee.price_unit, 15.0)

    def test_marketplace_import_is_allowed(self):
        """deltatech_marketplace_* update the lines with the platform price,
        under `from_marketplace` / `ignore_price_check`."""
        order, line = self._order(self.restricted)
        order.with_context(from_marketplace=True, ignore_price_check=True).write(
            {"order_line": [(1, line.id, {"price_unit": 95.0})]}
        )
        self.assertEqual(line.price_unit, 95.0)
        line.with_context(ignore_price_check=True).write({"price_unit": 96.0})
        self.assertEqual(line.price_unit, 96.0)

    def test_website_cart_is_allowed(self):
        """Website requests carry `website_id`: the shop prices the cart, e.g. the
        extra lines of deltatech_sale_add_extra_line on cart update."""
        order, line = self._order(self.restricted)
        line.with_context(website_id=1).write({"price_unit": 25.0})
        self.assertEqual(line.price_unit, 25.0)

    def test_restricted_user_can_update_prices(self):
        """ "Update prices" is an automatic repricing and stays allowed."""
        order, line = self._order(self.restricted)
        self.product.list_price = 110.0
        order.with_user(self.restricted).action_update_prices()
        self.assertEqual(line.price_unit, 110.0)

    def test_ordinary_seller_can_change_price(self):
        order, line = self._order(self.seller, {"price_unit": 120.0})
        line.write({"price_unit": 130.0, "discount": 10.0})
        self.assertEqual(line.price_unit, 130.0)
        self.assertEqual(line.discount, 10.0)
