# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestCreateRule(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.product"].create({"name": "Test product", "type": "product"})

    def test_create_rule(self):
        self.product.create_rule()
        self.assertTrue(self.product.orderpoint_ids)

    def test_create_product(self):
        product = self.env["product.product"].create({"name": "Test product", "type": "product"})
        self.assertTrue(product.orderpoint_ids)
