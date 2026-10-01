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
                # above the cost of the extra product (100): a lower price would raise
                # the below-cost warning of deltatech_sale_margin when installed
                extra_line_form.price_unit = 120.0
        self.assertEqual(extra_line.price_unit, 120.0)
        self.assertTrue(extra_line._has_manual_price())

        # the quantity keeps following the main line, the price does not
        with Form(order) as order_form:
            with order_form.order_line.edit(0) as main_line_form:
                main_line_form.product_uom_qty = 200
        self.assertEqual(extra_line.product_uom_qty, 200)
        self.assertEqual(extra_line.price_unit, 120.0)

        # not even when the price of the main line changes
        with Form(order) as order_form:
            with order_form.order_line.edit(0) as main_line_form:
                main_line_form.price_unit = 300
        self.assertEqual(extra_line.price_unit, 120.0)

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
        # a currency of our own, so that the test does not depend on the currency of the
        # company: `1 company currency = 0.25 TCU`
        test_currency = self.env["res.currency"].create(
            {
                "name": "TCU",
                "symbol": "TCU",
                "rate_ids": [(0, 0, {"rate": 0.25, "company_id": self.env.company.id})],
            }
        )
        pricelist_tcu = self.env["product.pricelist"].create({"name": "Test TCU", "currency_id": test_currency.id})

        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "pricelist_id": pricelist_tcu.id,
                "order_line": [(0, 0, {"product_id": self.product_b.id, "product_uom_qty": 100})],
            }
        )
        self.assertEqual(order.currency_id, test_currency)
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

    def _product_with_extra(self, name, extra_product, percent=10):
        return self.env["product.product"].create(
            {
                "name": name,
                "list_price": 200,
                "extra_product_id": extra_product.id if extra_product else False,
                "extra_percent": percent,
            }
        )

    def test_change_main_product_replaces_extra_line(self):
        """SALEEXTRA-001: a main product that requires another extra product replaces
        the extra line, instead of keeping the old one with an updated quantity."""
        extra_y = self.env["product.product"].create({"name": "Extra Y", "list_price": 40})
        product_c = self._product_with_extra("Test C", extra_y, percent=20)
        order = self._new_order()

        with Form(order) as order_form:
            with order_form.order_line.edit(0) as main_line_form:
                main_line_form.product_id = product_c

        self.assertFalse(self._extra_line(order), "the extra line of the old main product is gone")
        main_line = order.order_line.filtered(lambda li: li.product_id == product_c)
        extra_line = order.order_line.filtered(lambda li: li.product_id == extra_y)
        self.assertEqual(len(order.order_line), 2)
        self.assertEqual(len(extra_line), 1)
        self.assertEqual(extra_line.product_uom_qty, 100)
        self.assertEqual(extra_line.line_uuid, main_line.line_uuid)
        # the price is the computed one of the new extra product, not the old line's
        self.assertAlmostEqual(extra_line.price_unit, main_line.price_unit * 0.20)
        self.assertFalse(extra_line._has_manual_price())

    def test_change_main_product_replaces_manually_priced_extra_line(self):
        """A manual price belongs to the old extra product: it is not carried over."""
        extra_y = self.env["product.product"].create({"name": "Extra Y", "list_price": 40})
        product_c = self._product_with_extra("Test C", extra_y, percent=20)
        order = self._new_order()
        self._extra_line(order).price_unit = 7.0

        main_line = self._main_line(order)
        main_line.product_id = product_c
        main_line.check_extra_product()

        self.assertFalse(self._extra_line(order))
        extra_line = order.order_line.filtered(lambda li: li.product_id == extra_y)
        self.assertEqual(len(extra_line), 1)
        self.assertAlmostEqual(extra_line.price_unit, main_line.price_unit * 0.20)

    def test_change_main_product_to_product_without_extra_removes_extra_line(self):
        """SALEEXTRA-001: a main product with no extra product drops the extra line."""
        product_c = self._product_with_extra("Test C", False)
        order = self._new_order()

        with Form(order) as order_form:
            with order_form.order_line.edit(0) as main_line_form:
                main_line_form.product_id = product_c

        self.assertEqual(order.order_line.product_id, product_c)
        self.assertFalse(self._extra_line(order))

    def test_delete_main_line_after_extra_config_removed(self):
        """SALEEXTRA-001: deleting the main line removes its extra line even when the
        main product no longer requires one."""
        order = self._new_order()
        self.assertTrue(self._extra_line(order))
        self.product_b.extra_product_id = False

        self._main_line(order).unlink()

        self.assertFalse(order.order_line, "no orphan extra line is left behind")

    def test_delete_extra_line_keeps_main_line(self):
        """Deleting the extra line alone does not take the main line with it."""
        self.product_a.extra_product_id = self.product_b
        order = self._new_order()
        self._extra_line(order).unlink()
        self.assertEqual(order.order_line.product_id, self.product_b)
        self.assertFalse(self._extra_line(order))

    def test_extra_line_is_flagged(self):
        """The generated line is flagged, the main line is not."""
        order = self._new_order()
        self.assertTrue(self._extra_line(order).is_extra_line)
        self.assertFalse(self._main_line(order).is_extra_line)

    def test_form_delete_both_lines(self):
        """Removing the main and the extra line in the form deletes both on save."""
        order = self._new_order()
        with Form(order) as order_form:
            order_form.order_line.remove(0)
            order_form.order_line.remove(0)
        self.assertFalse(order.order_line)
