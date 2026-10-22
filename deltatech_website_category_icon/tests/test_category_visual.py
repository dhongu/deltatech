# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import io
from unittest.mock import patch

from PIL import Image

from odoo.tests import HttpCase, TransactionCase, tagged

ICON = '<svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="21" fill="#1d5c33"/></svg>'
PARENT_ICON = '<svg viewBox="0 0 64 64"><rect x="8" y="8" width="48" height="48" fill="#1d5c33"/></svg>'


def png(color="green"):
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue())


@tagged("post_install", "-at_install")
class TestCategoryVisual(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env["product.public.category"]
        cls.website = cls.env["website"].get_current_website()
        cls.svg_and_image = Category.create({"name": "TB Visual Both", "icon_svg": ICON, "image_1920": png()})
        cls.image_only = Category.create({"name": "TB Visual Image", "image_1920": png("red")})
        cls.parent = Category.create({"name": "TB Visual Parent", "icon_svg": PARENT_ICON})
        cls.child_with_image = Category.create(
            {"name": "TB Visual Child", "parent_id": cls.parent.id, "image_1920": png("blue")}
        )
        cls.empty = Category.create({"name": "TB Visual Empty"})
        cls.empty_sub = Category.create({"name": "TB Visual Empty Sub", "parent_id": cls.empty.id})
        Product = cls.env["product.template"]
        cls.product = Product.create(
            {
                "name": "TB Visual Product",
                "is_published": True,
                "sale_ok": True,
                "image_1920": png("yellow"),
                "website_sequence": 1,
                "public_categ_ids": [(6, 0, cls.empty_sub.ids)],
            }
        )
        # Neither unpublished products nor products without a picture are shown.
        Product.create(
            {
                "name": "TB Visual Hidden",
                "is_published": False,
                "sale_ok": True,
                "image_1920": png("black"),
                "website_sequence": 0,
                "public_categ_ids": [(6, 0, cls.empty.ids)],
            }
        )
        Product.create(
            {
                "name": "TB Visual No Picture",
                "is_published": True,
                "sale_ok": True,
                "website_sequence": 0,
                "public_categ_ids": [(6, 0, cls.empty.ids)],
            }
        )

    def _kinds(self, category, **kwargs):
        kinds = {}
        for order in ("svg_image_product", "image_svg_product", "svg_image", "image_svg"):
            self.website.category_icon_order = order
            kinds[order] = category.tb_category_visual(self.website, **kwargs)["kind"]
        return kinds

    def test_default_order(self):
        # The default adds no product pictures to existing shops.
        self.assertEqual(self.env["website"].create({"name": "TB Visual Website"}).category_icon_order, "svg_image")

    def test_svg_and_image(self):
        self.assertEqual(
            self._kinds(self.svg_and_image),
            {"svg_image_product": "svg", "image_svg_product": "image", "svg_image": "svg", "image_svg": "image"},
        )
        self.website.category_icon_order = "svg_image"
        visual = self.svg_and_image.tb_category_visual(self.website)
        self.assertEqual(str(visual["svg"]), self.svg_and_image.icon_svg)
        self.website.category_icon_order = "image_svg"
        visual = self.svg_and_image.tb_category_visual(self.website, "image_256")
        self.assertIn(f"/web/image/product.public.category/{self.svg_and_image.id}/image_256", visual["url"])

    def test_image_only(self):
        self.assertEqual(set(self._kinds(self.image_only).values()), {"image"})

    def test_parent_svg(self):
        # The parent's icon stands for the category's own icon.
        self.assertEqual(
            self._kinds(self.child_with_image),
            {"svg_image_product": "svg", "image_svg_product": "image", "svg_image": "svg", "image_svg": "image"},
        )
        self.website.category_icon_order = "svg_image"
        self.assertEqual(str(self.child_with_image.tb_category_visual(self.website)["svg"]), self.parent.icon_svg)
        # Without inheritance (left category list, option "All categories") the image comes first.
        self.assertEqual(set(self._kinds(self.child_with_image, inherit_svg=False).values()), {"image"})

    def test_first_product(self):
        self.assertEqual(
            self._kinds(self.empty),
            {"svg_image_product": "product", "image_svg_product": "product", "svg_image": False, "image_svg": False},
        )
        self.website.category_icon_order = "svg_image_product"
        visual = self.empty.tb_category_visual(self.website)
        self.assertIn(f"/web/image/product.template/{self.product.id}/image_128", visual["url"])
        self.assertIsNone(visual["svg"])

    def test_nothing_found(self):
        self.product.is_published = False
        self.assertEqual(set(self._kinds(self.empty).values()), {False})
        self.assertEqual(
            self.empty.tb_category_visual(self.website),
            {"kind": False, "svg": None, "url": None},
        )

    def test_order_clears_cache(self):
        # Renderings cached from shop data (the automatic category menu of
        # deltatech_website_shop_snippets) follow the option: website.write clears them.
        with patch.object(type(self.env.registry), "clear_cache") as clear_cache:
            self.website.category_icon_order = "image_svg_product"
        clear_cache.assert_called()


@tagged("post_install", "-at_install")
class TestCategoryVisualShop(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("website_sale.products_categories").active = True
        cls.env.ref("website_sale.products_categories_top").active = True
        Category = cls.env["product.public.category"]
        cls.website = cls.env["website"].get_current_website()
        cls.root = Category.create({"name": "TB Visual Root", "image_1920": png()})
        cls.sub = Category.create({"name": "TB Visual Sub", "parent_id": cls.root.id})
        cls.product = cls.env["product.template"].create(
            {
                "name": "TB Visual Shop Product",
                "is_published": True,
                "sale_ok": True,
                "image_1920": png("yellow"),
                "public_categ_ids": [(6, 0, cls.sub.ids)],
            }
        )

    def test_image_in_category_list(self):
        page = self.url_open("/shop").text
        self.assertRegex(
            page,
            r'<img class="o_category_image o_category_icon_sm rounded"[^>]*'
            rf'src="/web/image/product.public.category/{self.root.id}/image_128',
        )
        self.website.category_icon_order = "svg_image"
        self.root.icon_svg = ICON
        page = self.url_open("/shop").text
        self.assertNotIn(f"/web/image/product.public.category/{self.root.id}/image_128", page)
        self.assertIn('<circle cx="32" cy="32" r="21" fill="#1d5c33"/>', page)

    def test_product_in_filmstrip(self):
        # all_products: the category page of deltatech_website_sale_category (a page of
        # subcategories) is skipped when that module is installed.
        slug = self.env["ir.http"]._slug(self.root)
        product_url = f"/web/image/product.template/{self.product.id}/image_128"
        self.website.category_icon_order = "svg_image"
        page = self.url_open(f"/shop/category/{slug}?all_products=1").text
        self.assertIn('name="o_wsale_filmstrip_placeholder"', page)
        self.assertNotIn(product_url, page)
        self.website.category_icon_order = "svg_image_product"
        page = self.url_open(f"/shop/category/{slug}?all_products=1").text
        self.assertNotIn('name="o_wsale_filmstrip_placeholder"', page)
        self.assertRegex(page, rf"background-image:url\((&#39;|'){product_url}")
