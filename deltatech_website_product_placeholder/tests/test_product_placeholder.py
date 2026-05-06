from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductPlaceholder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].create(
            {
                "name": "Test Website",
            }
        )
        cls.product_tmpl = cls.env["product.template"].create(
            {
                "name": "Test Product Template",
                "image_1920": False,
            }
        )
        cls.product_variant = cls.product_tmpl.product_variant_id

    def test_01_placeholder_filename_default(self):
        """Test if the default placeholder is returned when no custom image is set on website"""
        # We need to simulate the current website context
        self.product_tmpl = self.product_tmpl.with_context(website_id=self.website.id)
        filename = self.product_tmpl._get_placeholder_filename("image_1920")
        self.assertEqual(filename, "deltatech_website_product_placeholder/static/img/placeholder.png")

    def test_02_placeholder_filename_custom(self):
        """Test if the custom placeholder is returned when set on website"""
        # Set a custom image on the website (minimal valid 1x1 PNG)
        image_content = (
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        self.website.product_placeholder_image = image_content

        # Simulate current website context
        self.product_tmpl = self.product_tmpl.with_context(website_id=self.website.id)

        filename = self.product_tmpl._get_placeholder_filename("image_1920")
        expected_filename = f"website/{self.website.id}/product_placeholder_image"
        self.assertEqual(filename, expected_filename)

    def test_03_qweb_field_image_urls(self):
        """Test if QWeb field image generator returns the correct URLs for products without images"""
        FieldImage = self.env["ir.qweb.field.image"]

        # Case 1: Default placeholder
        self.website.product_placeholder_image = False
        product = self.product_tmpl.with_context(website_id=self.website.id)

        url, _ = FieldImage._get_src_urls(product, "image_1920", {})
        self.assertEqual(url, "/deltatech_website_product_placeholder/static/img/placeholder.png")

        # Case 2: Custom placeholder
        image_content = (
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        self.website.product_placeholder_image = image_content

        url, _ = FieldImage._get_src_urls(product, "image_1920", {})
        expected_url = f"/web/image/website/{self.website.id}/product_placeholder_image"
        self.assertEqual(url, expected_url)

    def test_04_product_with_image(self):
        """Test that products with real images still use the standard Odoo URLs"""
        image_content = (
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        self.product_tmpl.image_1920 = image_content

        FieldImage = self.env["ir.qweb.field.image"]
        product = self.product_tmpl.with_context(website_id=self.website.id)

        # For products with image, it should fall back to super() which generates standard web/image URL
        url, _ = FieldImage._get_src_urls(product, "image_1920", {})
        self.assertTrue(url.startswith("/web/image/product.template/"))
        self.assertIn("/image_1920", url)
