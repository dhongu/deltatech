# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests.common import TransactionCase


class TestCatalog(TransactionCase):
    def setUp(self):
        super(TestCatalog, self).setUp()

        test_category = self.env["product.category"].create(
            {
                "name": "test category",
            }
        )
        values = {
            "name": "Product 1",
            "code": "Code1",
            "list_price": 5,
            "purchase_price": 2,
            "categ_id": test_category.id,
        }
        self.catalog1 = self.env["product.catalog"].create(values)
        values = {
            "name": "Product 2",
            "code": "Code2",
            "list_price": 5,
            "purchase_price": 2,
            "categ_id": test_category.id,
        }
        self.catalog2 = self.env["product.catalog"].create(values)

    def test_create_product(self):
        prod1 = self.catalog1.create_product()
        self.assertEqual(prod1.name, "Product 1")

    def test_search_product(self):
        prod2 = self.env["product.product"].name_search("Code2")
        self.assertEqual(prod2[0][1], "[Code2] Product 2")
