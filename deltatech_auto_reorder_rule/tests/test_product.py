# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestCreateRule(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.product"].create(
            {"name": "Test product", "type": "consu", "is_storable": True}
        )

    def test_create_rule(self):
        self.product.create_rule()
        self.assertTrue(self.product.orderpoint_ids)

    def test_create_product(self):
        product = self.env["product.product"].create({"name": "Test product", "type": "consu", "is_storable": True})
        self.assertTrue(product.orderpoint_ids)

    def test_no_rule_for_non_storable(self):
        product = self.env["product.product"].create({"name": "Test consumable", "type": "consu"})
        self.assertFalse(product.orderpoint_ids)
