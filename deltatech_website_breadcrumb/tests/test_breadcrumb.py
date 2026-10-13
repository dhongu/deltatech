# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteBreadcrumb(TransactionCase):
    def test_templates_exist(self):
        """Test that breadcrumb templates are installed"""
        template_product = self.env.ref("deltatech_website_breadcrumb.product", raise_if_not_found=False)
        self.assertTrue(template_product, "Template 'product' does not exist")

        template_breadcrumb = self.env.ref("deltatech_website_breadcrumb.breadcrumb", raise_if_not_found=False)
        self.assertTrue(template_breadcrumb, "Template 'breadcrumb' does not exist")

        template_recursive = self.env.ref("deltatech_website_breadcrumb.breadcrumb_recursive", raise_if_not_found=False)
        self.assertTrue(template_recursive, "Template 'breadcrumb_recursive' does not exist")

    def test_product_with_category_breadcrumb(self):
        """Test that a product with a public category can be used for breadcrumb"""
        # Create a public category
        category = self.env["product.public.category"].create({"name": "Test Category"})

        # Create a product with the category
        product = self.env["product.template"].create(
            {
                "name": "Test Breadcrumb Product",
                "public_categ_ids": [(4, category.id)],
            }
        )

        self.assertEqual(len(product.public_categ_ids), 1)
        self.assertEqual(product.public_categ_ids[0].id, category.id)

    def test_product_with_nested_category_breadcrumb(self):
        """Test that a product with nested categories works for breadcrumb"""
        parent_category = self.env["product.public.category"].create({"name": "Parent Category"})
        child_category = self.env["product.public.category"].create(
            {"name": "Child Category", "parent_id": parent_category.id}
        )

        product = self.env["product.template"].create(
            {
                "name": "Test Nested Breadcrumb Product",
                "public_categ_ids": [(4, child_category.id)],
            }
        )

        self.assertEqual(len(product.public_categ_ids), 1)
        self.assertTrue(product.public_categ_ids[0].parent_id, "Child category should have a parent")
        self.assertEqual(product.public_categ_ids[0].parent_id.id, parent_category.id)
