# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProduct(TransactionCase):
    def setUp(self):
        super().setUp()
        # Setare paramentru deltatech_alternative_website.search_index
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("deltatech_alternative_website.search_index", "True")

    def test_create_product(self):
        product = Form(self.env["product.template"])
        product.name = "Test Product"
        product.default_code = "CODE1"
        product.alternative_code = "CODE2"
        product = product.save()

        product.name_search("CODE2")
