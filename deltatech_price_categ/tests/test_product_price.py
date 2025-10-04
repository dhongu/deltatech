# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPriceCateg(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.template"].create(
            {
                "name": "test",
                "list_price": 200,
                "standard_price": 50,
                "last_purchase_price": 60,
            }
        )

    def test_price_categ_by_last_purchase_price(self):
        product = Form(self.product)
        product.list_price_base = "last_purchase_price"
        product.percent_bronze = 0.80
        product.percent_copper = 0.70
        product.percent_silver = 0.60
        product.percent_gold = 0.50
        product.save()

    def test_price_categ_by_standard_price(self):
        product = Form(self.product)
        product.list_price_base = "standard_price"
        product.percent_bronze = 0.80
        product.percent_copper = 0.70
        product.percent_silver = 0.60
        product.percent_gold = 0.50
        product.save()

    def test_price_categ_by_list_price(self):
        product = Form(self.product)
        product.list_price_base = "list_price"
        product.percent_bronze = -0.25
        product.percent_copper = -0.30
        product.percent_silver = -0.35
        product.percent_gold = -0.40
        product.save()

    def test_get_get_combination_info(self):
        self.product._get_combination_info()
