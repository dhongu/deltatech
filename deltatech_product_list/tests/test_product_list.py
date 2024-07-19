from odoo.tests import common


class TestProductList(common.TransactionCase):

    def setUp(self):
        super().setUp()

        # Create a product list
        self.product_list = self.env["product.list"].create(
            {
                "name": "Test Product List",
                "products_domain": "[['sale_ok', '=', True]]",
                "active": True,
                "limit": 80,
                "company_id": self.env.company.id,
            }
        )

    def test_product_list_creation(self):
        # Check if the product list was created
        self.assertTrue(self.product_list, "Product List was not created")

        # Check the name of the product list
        self.assertEqual(self.product_list.name, "Test Product List", "Product List name is not correct")

        # Check the products_domain of the product list
        self.assertEqual(
            self.product_list.products_domain, "[['sale_ok', '=', True]]", "Product List products_domain is not correct"
        )

        # Check the active status of the product list
        self.assertTrue(self.product_list.active, "Product List is not active")

        # Check the limit of the product list
        self.assertEqual(self.product_list.limit, 80, "Product List limit is not correct")

        # Check the company of the product list
        self.assertEqual(self.product_list.company_id, self.env.company, "Product List company is not correct")
