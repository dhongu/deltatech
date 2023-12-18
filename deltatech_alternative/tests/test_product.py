# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProduct(TransactionCase):
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

        product._name_search("CODE2", domain=None, operator="ilike", limit=100)
        self.set_param("deltatech_alternative_website.search_index", "False")
        product._name_search("CODE2", domain=None, operator="ilike", limit=100)

    def test_create_product_product(self):
        product = Form(self.env["product.product"])
        product.name = "Test Product"
        product.default_code = "CODE1"
        product.alternative_code = "CODE2"
        product = product.save()

        product._name_search("CODE2", domain=None, operator="ilike", limit=100)
        self.set_param("deltatech_alternative_website.search_index", "False")
        product._name_search("CODE2", domain=None, operator="ilike", limit=100)
