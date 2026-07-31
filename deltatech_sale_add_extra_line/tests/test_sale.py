# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSale(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "is_storable": True,
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
                "extra_product_id": self.product_a.id,
                "extra_percent": 10,
            }
        )

        self.stock_location = self.env.ref("stock.stock_location_stock")
        self.env["stock.quant"]._update_available_quantity(self.product_a, self.stock_location, 1000)
        self.env["stock.quant"]._update_available_quantity(self.product_b, self.stock_location, 1000)
        # inv_line_a = {
        #     "product_id": self.product_a.id,
        #     "product_qty": 10000,
        #     "location_id": self.stock_location.id,
        # }
        # inv_line_b = {
        #     "product_id": self.product_b.id,
        #     "product_qty": 10000,
        #     "location_id": self.stock_location.id,
        # }
        # inventory = self.env["stock.inventory"].create(
        #     {
        #         "name": "Inv. productserial1",
        #         "line_ids": [
        #             (0, 0, inv_line_a),
        #             (0, 0, inv_line_b),
        #         ],
        #     }
        # )
        # inventory.action_start()
        # inventory.action_validate()

    def _new_order(self, qty=100):
        so_form = Form(self.env["sale.order"])
        so_form.partner_id = self.partner_a
        with so_form.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = qty
        return so_form.save()

    def _extra_line(self, order):
        return order.order_line.filtered(lambda li: li.product_id == self.product_a)

    def _main_line(self, order):
        return order.order_line.filtered(lambda li: li.product_id == self.product_b)

    def test_sale(self):
        self.so = self._new_order()

    def test_extra_line_computed_price(self):
        """The extra line price comes from the percent set on the main product."""
        order = self._new_order()
        extra_line = self._extra_line(order)
        self.assertEqual(len(extra_line), 1)
        self.assertEqual(extra_line.product_uom_qty, 100)
        # 10% of the price of the main line
        self.assertAlmostEqual(extra_line.price_unit, self._main_line(order).price_unit * 0.10)
        self.assertFalse(extra_line._has_manual_price())

    def test_extra_line_manual_price_is_kept(self):
        """A price typed in on the extra line is no longer overwritten."""
        order = self._new_order()
        extra_line = self._extra_line(order)

        with Form(order) as order_form:
            with order_form.order_line.edit(1) as extra_line_form:
                extra_line_form.price_unit = 7.0
        self.assertEqual(extra_line.price_unit, 7.0)
        self.assertTrue(extra_line._has_manual_price())

        # the quantity keeps following the main line, the price does not
        with Form(order) as order_form:
            with order_form.order_line.edit(0) as main_line_form:
                main_line_form.product_uom_qty = 200
        self.assertEqual(extra_line.product_uom_qty, 200)
        self.assertEqual(extra_line.price_unit, 7.0)

        # not even when the price of the main line changes
        with Form(order) as order_form:
            with order_form.order_line.edit(0) as main_line_form:
                main_line_form.price_unit = 300
        self.assertEqual(extra_line.price_unit, 7.0)

    def test_extra_line_computed_price_follows_main_line(self):
        """Without a manual price, the extra line price follows the main line."""
        order = self._new_order()
        extra_line = self._extra_line(order)

        with Form(order) as order_form:
            with order_form.order_line.edit(0) as main_line_form:
                main_line_form.price_unit = 300
        self.assertEqual(extra_line.price_unit, 30.0)

    def test_extra_line_without_percent_follows_pricelist_currency(self):
        """Without a percent, the extra line keeps the standard price of its own
        product, so the pricelist currency applies."""
        self.product_b.extra_percent = 0.0
        currency_eur = self.env.ref("base.EUR")
        self.env["res.currency.rate"].create(
            {
                "currency_id": currency_eur.id,
                "company_id": self.env.company.id,
                "rate": 0.25,
            }
        )
        pricelist_eur = self.env["product.pricelist"].create({"name": "Test EUR", "currency_id": currency_eur.id})

        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "pricelist_id": pricelist_eur.id,
                "order_line": [(0, 0, {"product_id": self.product_b.id, "product_uom_qty": 100})],
            }
        )
        self.assertEqual(order.currency_id, currency_eur)
        main_line = order.order_line
        main_line.check_extra_product()
        extra_line = self._extra_line(order)
        # the 150 list price of product_a converted at the 0.25 rate, not the list price itself
        self.assertEqual(extra_line.price_unit, 37.5)
        self.assertFalse(extra_line._has_manual_price())

        # a manual price is still recognized and kept
        extra_line.price_unit = 7.0
        self.assertTrue(extra_line._has_manual_price())
        main_line.product_uom_qty = 200
        main_line.check_extra_product()
        self.assertEqual(extra_line.product_uom_qty, 200)
        self.assertEqual(extra_line.price_unit, 7.0)

    def test_extra_line_deleted_is_regenerated_with_computed_price(self):
        """Deleting the extra line is the way back to the computed price."""
        order = self._new_order()
        self._extra_line(order).unlink()

        with Form(order) as order_form:
            with order_form.order_line.edit(0) as main_line_form:
                main_line_form.product_uom_qty = 50
        extra_line = self._extra_line(order)
        self.assertEqual(len(extra_line), 1)
        self.assertEqual(extra_line.product_uom_qty, 50)
        self.assertAlmostEqual(extra_line.price_unit, self._main_line(order).price_unit * 0.10)
