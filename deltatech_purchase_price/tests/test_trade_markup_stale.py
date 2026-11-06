# See README.rst file on addons root folder for license details

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestTradeMarkupStale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("purchase.update_list_price", "False")
        cls.product = cls.env["product.template"].create(
            {
                "name": "Test markup",
                "is_storable": True,
                "taxes_id": [(6, 0, [])],
                "list_price": 23.38,
                "trade_markup": 12,
            }
        )

    def test_markup_follows_corrected_purchase_price(self):
        """Mistyped purchase price, then sale price and purchase price changed in the same edit."""
        form = Form(self.product)
        form.last_purchase_price = 1300
        product = form.save()
        self.assertEqual(product.list_price, 23.38)

        form = Form(product)
        form.list_price = 23.02
        self.assertAlmostEqual(form.trade_markup, -98.23, places=2)
        form.last_purchase_price = 20.93
        product = form.save()

        self.assertEqual(product.list_price, 23.02)
        self.assertAlmostEqual(product.trade_markup, (23.02 - 20.93) / 20.93 * 100, places=2)

    def test_manual_markup_is_kept(self):
        """Typing the markup by hand must not be overwritten from the sale price."""
        form = Form(self.product)
        form.last_purchase_price = 20
        form.trade_markup = 30
        product = form.save()
        self.assertEqual(product.trade_markup, 30)

    def test_update_list_price_on_keeps_markup(self):
        """With the automatic sale price update, the markup drives the sale price as before."""
        self.env["ir.config_parameter"].sudo().set_param("purchase.update_list_price", "True")
        form = Form(self.product)
        form.last_purchase_price = 20
        product = form.save()
        self.assertAlmostEqual(product.trade_markup, 12, places=2)
        self.assertAlmostEqual(product.list_price, 22.4, places=2)
