# ©  2025 Terrabit
#              Voicu Stefan <stefan(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

# 1x1 px PNG valid (imagine pentru image_1920)
IMG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGM4wcAAAAJcAMlDyBJGAAAAAElFTkSuQmCC"


@tagged("post_install", "-at_install")
class TestProductVisibility(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.template"]
        cls.category = cls.env["product.public.category"].create({"name": "Test categ"})

    def _make_full_product(self):
        product = self.Product.create(
            {
                "name": "Produs complet",
                "default_code": "SKU-001",
                "list_price": 100.0,
                "image_1920": IMG,
                "website_description": "<p>Descriere amplă cu specificații.</p>",
                "description_ecommerce": "<p>Descriere scurtă.</p>",
                "website_meta_title": "Titlu SEO",
                "website_meta_description": "Descriere SEO",
                "website_meta_keywords": "cuvinte, cheie",
                "public_categ_ids": [(4, self.category.id)],
            }
        )
        self.env["product.image"].create(
            [
                {"name": "img1", "image_1920": IMG, "product_tmpl_id": product.id},
                {"name": "img2", "image_1920": IMG, "product_tmpl_id": product.id},
            ]
        )
        return product

    def test_empty_product_is_hidden(self):
        product = self.Product.create({"name": "Produs gol"})
        self.assertLess(product.website_visibility_score, 40)
        self.assertEqual(product.website_visibility_level, "hidden")

    def test_full_product_is_optimal(self):
        product = self._make_full_product()
        # galeria se calculează la crearea imaginilor -> forțăm reevaluarea
        product.invalidate_recordset()
        self.assertEqual(product.website_visibility_score, 100)
        self.assertEqual(product.website_visibility_level, "optimal")

    def test_partial_product_is_good(self):
        # SEO(25) + imagine(18) + descriere website(15) + categorie(12) + preț(5) = 75
        product = self.Product.create(
            {
                "name": "Produs parțial",
                "list_price": 50.0,
                "image_1920": IMG,
                "website_description": "<p>Descriere.</p>",
                "website_meta_title": "T",
                "website_meta_description": "D",
                "website_meta_keywords": "k",
                "public_categ_ids": [(4, self.category.id)],
            }
        )
        self.assertEqual(product.website_visibility_score, 75)
        self.assertEqual(product.website_visibility_level, "good")

    def test_recompute_action(self):
        criterion = self.env.ref("deltatech_product_visibility.criterion_seo")
        criterion.action_recompute_scores()
