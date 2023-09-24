# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProduct(TransactionCase):
    def test_create_product(self):
        product = Form(self.env["product.template"])
        product.name = "Test Product"
        product.default_code = "CODE1"
        product.alternative_code = "CODE2"
        product = product.save()

        product.name_search("CODE2")
