from odoo.tests.common import TransactionCase


class TestProductCatalogReport(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a product category
        self.public_category = self.env["product.public.category"].create(
            {
                "name": "Public Test Category",
            }
        )

        # Create a product associated with the product category
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "public_categ_ids": [(6, 0, [self.public_category.id])],
            }
        )

    def test_product_catalog_report(self):
        # Get the ProductCatalogReport record
        product_catalog_report = self.env["report.deltatech_product_catalog.report_product_catalog"]

        # Call the _get_report_values method
        values = product_catalog_report._get_report_values([self.product.id])

        # Check the docs field
        self.assertEqual(values["docs"], self.product, "The docs field should be the product")

    def test_category_catalog_report(self):
        # Get the CategoryCatalogReport record
        category_catalog_report = self.env["report.deltatech_product_catalog.report_category_catalog"]

        # Call the _get_report_values method
        category_catalog_report._get_report_values([self.public_category.id])

        # Check the docs field
