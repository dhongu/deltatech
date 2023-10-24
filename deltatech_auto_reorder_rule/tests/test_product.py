# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestProduct(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        self.seller_ids = [(0, 0, {"name": self.partner_a.id})]

    def test_create_product(self):
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": self.seller_ids,
            }
        )
