# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import re

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteBreadcrumb(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].get_current_website()
        Category = cls.env["product.public.category"]
        cls.parent = Category.create({"name": "TB Breadcrumb Parent"})
        cls.child = Category.create({"name": "TB Breadcrumb Child", "parent_id": cls.parent.id})
        Template = cls.env["product.template"]
        values = {"sale_ok": True, "is_published": True, "website_id": False}
        cls.with_category = Template.create(
            dict(values, name="TB Breadcrumb Product", public_categ_ids=[(6, 0, cls.child.ids)])
        )
        cls.without_category = Template.create(dict(values, name="TB Breadcrumb Lonely"))

    def _breadcrumb(self, product):
        html = self.url_open(product.website_url).text
        match = re.search(r'<ol class="breadcrumb">(.*?)</ol>', html, re.S)
        self.assertTrue(match, "No breadcrumb on the product page")
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match.group(1))).strip()

    def test_category_trail_and_name(self):
        text = self._breadcrumb(self.with_category)
        self.assertIn("TB Breadcrumb Parent", text)
        self.assertIn("TB Breadcrumb Child", text)
        self.assertTrue(text.endswith("TB Breadcrumb Product"), text)

    def test_without_category_shows_products(self):
        text = self._breadcrumb(self.without_category)
        self.assertTrue(text.startswith("Products"), text)
        self.assertIn("TB Breadcrumb Lonely", text)

    def test_product_name_switched_off(self):
        self.website.breadcrumb_show_product_name = False
        text = self._breadcrumb(self.with_category)
        self.assertNotIn("TB Breadcrumb Product", text)
        self.assertIn("TB Breadcrumb Child", text)
        # Without a category only Products is left, not the name repeated by the title.
        self.assertEqual(self._breadcrumb(self.without_category), "Products")

    def test_category_choice(self):
        self.assertEqual(self.with_category._breadcrumb_category(), self.child)
        self.assertFalse(self.without_category._breadcrumb_category())
        other = self.env["product.public.category"].create({"name": "TB Breadcrumb Other"})
        self.with_category.public_categ_ids = [(6, 0, (other | self.child).ids)]
        if "tb_menu_hidden" not in other._fields:
            self.skipTest("tb_menu_hidden needs deltatech_website_shop_snippets")
        # A category kept out of the category menu (campaign) is passed over.
        other.tb_menu_hidden = True
        self.assertEqual(self.with_category._breadcrumb_category(), self.child)
