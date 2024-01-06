from odoo.tests.common import TransactionCase


class TestProduct(TransactionCase):
    def setUp(self):
        super().setUp()

        test_category = self.env["product.category"].create({"name": "test category"})
        values = {
            "name": "Product 1",
            "default_code": "Code1",
            "list_price": 5,
            "categ_id": test_category.id,
            "alternative_ids": [
                (0, 0, {"name": "Code2"}),
                (0, 0, {"name": "Code3"}),
                (0, 0, {"name": "Code4"}),
            ],
        }
        self.product1 = self.env["product.product"].create(values)
        values = {
            "name": "Product 2",
            "default_code": "CodeZ",
            "list_price": 5,
            "categ_id": test_category.id,
            "alternative_ids": [
                (0, 0, {"name": "CodeA"}),
                (0, 0, {"name": "CodeB"}),
                (0, 0, {"name": "CodeC"}),
            ],
        }
        self.product2 = self.env["product.product"].create(values)

    def test_alternative_code(self):
        self.assertEqual(self.product1.alternative_code, "Code2; Code3; Code4")
        self.assertEqual(self.product2.alternative_code, "CodeA; CodeB; CodeC")

    def test_search_product(self):
        prod1 = self.env["product.product"].name_search("Code3")
        self.assertEqual(prod1[0][1], "[Code1] Product 1")
        prod2 = self.env["product.product"].name_search("CodeA")
        self.assertEqual(prod2[0][1], "[CodeZ] Product 2")


class TestProductTemplate(TransactionCase):
    def setUp(self):
        super().setUp()

        test_category = self.env["product.category"].create({"name": "test category"})
        values = {
            "name": "Product 1",
            "default_code": "Code1",
            "list_price": 5,
            "categ_id": test_category.id,
            "alternative_ids": [
                (0, 0, {"name": "Code2"}),
                (0, 0, {"name": "Code3"}),
                (0, 0, {"name": "Code4"}),
            ],
        }
        self.product1 = self.env["product.template"].create(values)
        values = {
            "name": "Product 2",
            "default_code": "CodeZ",
            "list_price": 5,
            "categ_id": test_category.id,
            "alternative_ids": [
                (0, 0, {"name": "CodeA"}),
                (0, 0, {"name": "CodeB"}),
                (0, 0, {"name": "CodeC"}),
            ],
        }
        self.product2 = self.env["product.template"].create(values)

    def test_alternative_code(self):
        self.assertEqual(self.product1.alternative_code, "Code2; Code3; Code4")
        self.assertEqual(self.product2.alternative_code, "CodeA; CodeB; CodeC")

    def test_search_product(self):
        prod1 = self.env["product.template"].name_search("Code3")
        self.assertEqual(prod1[0][1], "[Code1] Product 1")
        prod2 = self.env["product.template"].name_search("CodeA")
        self.assertEqual(prod2[0][1], "[CodeZ] Product 2")
