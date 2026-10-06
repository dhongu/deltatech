# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSellerDefaultPrice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.template = cls.env["product.template"].create(
            {"name": "Test Product", "is_storable": True, "standard_price": 99.01}
        )

    def test_template_new_seller_line_price_zero(self):
        with Form(self.template, view="purchase.view_product_supplier_inherit") as form:
            with form.seller_ids.new() as line:
                line.partner_id = self.vendor
                self.assertEqual(line.price, 0.0)
        self.assertEqual(self.template.seller_ids.price, 0.0)

    def test_variant_new_seller_line_price_zero(self):
        variant = self.template.product_variant_id
        with Form(variant, view="purchase.view_product_product_supplier_inherit") as form:
            with form.seller_ids.new() as line:
                line.partner_id = self.vendor
                self.assertEqual(line.price, 0.0)
