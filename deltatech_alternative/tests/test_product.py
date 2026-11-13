# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProduct(TransactionCase):

    def test_alternative_code_cache_refresh(self):
        product = self.env["product.template"].create({"name": "Test ALT-002"})
        alt1 = self.env["product.alternative"].create({"name": "A1", "product_tmpl_id": product.id})
        alt2 = self.env["product.alternative"].create({"name": "A2", "product_tmpl_id": product.id})
        variant = product.product_variant_id
        self.assertEqual(product.alternative_code, "A1; A2")  # pune valoarea în cache

        alt1.name = "B1"
        self.assertEqual(product.alternative_code, "B1; A2")
        self.assertEqual(variant.alternative_code, "B1; A2")

        alt2.hide = True
        self.assertEqual(product.alternative_code, "B1")

        alt2.hide = False
        self.assertEqual(product.alternative_code, "B1; A2")

        alt1.unlink()
        self.assertEqual(product.alternative_code, "A2")

    def setUp(self):
        super().setUp()
        # Setare paramentru deltatech_alternative_website.search_index
        self.set_param = self.env["ir.config_parameter"].sudo().set_param
        self.set_param("deltatech_alternative_website.search_index", "True")

    def test_create_product_template(self):
        product = Form(self.env["product.template"])
        product.name = "Test Product"
        product.default_code = "CODE1"
        product.alternative_code = "CODE2"
        product = product.save()

        product.name_search("CODE2", operator="ilike", limit=100)
        self.set_param("deltatech_alternative_website.search_index", "False")
        product.name_search("CODE2", operator="ilike", limit=100)

    def test_create_product_product(self):
        product = Form(self.env["product.product"])
        product.name = "Test Product"
        product.default_code = "CODE1"
        product.alternative_code = "CODE2"
        product = product.save()

        product.name_search("CODE2", operator="ilike", limit=100)
        self.set_param("deltatech_alternative_website.search_index", "False")
        product.name_search("CODE2", operator="ilike", limit=100)
