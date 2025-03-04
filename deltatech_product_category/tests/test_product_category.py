from odoo.tests.common import TransactionCase


class TestProductCategory(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a company
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

        # Create a product category associated with the company
        self.product_category = self.env["product.category"].create(
            {
                "name": "Test Category",
                "company_id": self.company.id,
            }
        )

        # Create a product associated with the company
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "company_id": self.company.id,
            }
        )

    def test_company_id(self):
        # Check the company_id field of the product category and product
        self.assertEqual(
            self.product_category.company_id,
            self.company,
            "The company_id field of the product category should be the company",
        )
        self.assertEqual(
            self.product.company_id, self.company, "The company_id field of the product should be the company"
        )

    def test_res_config_settings(self):
        # Get the res.config.settings record
        res_config_settings = self.env["res.config.settings"].create({})

        # Call the get_values method
        values = res_config_settings.get_values()

        # Check the company_share_product_category field
        self.assertEqual(
            values["company_share_product_category"], True, "The company_share_product_category field should be True"
        )

        # Call the set_values method
        res_config_settings.write({"company_share_product_category": False})
        res_config_settings.set_values()

        # Call the get_values method again
        values = res_config_settings.get_values()

        # Check the company_share_product_category field
        self.assertEqual(
            values["company_share_product_category"], False, "The company_share_product_category field should be False"
        )
