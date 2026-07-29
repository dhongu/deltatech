# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestLazyCategories(HttpCase):
    """The shop sidebar must ship only the open branch of the category tree."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # The left category column and its collapsible variant are optional
        # views, both off in a fresh database. The lazy rendering only applies
        # to the collapsible one, so enable both.
        cls.env.ref("website_sale.products_categories").active = True
        cls.env.ref("website_sale.option_collapse_products_categories").active = True

        Category = cls.env["product.public.category"]
        cls.root = Category.create({"name": "TB Root Category"})
        cls.child = Category.create({"name": "TB Child Category", "parent_id": cls.root.id})
        cls.grandchild = Category.create({"name": "TB Grandchild Category", "parent_id": cls.child.id})

        cls.product = cls.env["product.template"].create(
            {
                "name": "TB Lazy Product",
                "is_published": True,
                "list_price": 10.0,
                "public_categ_ids": [(6, 0, cls.grandchild.ids)],
            }
        )

    def test_shop_page_omits_collapsed_branches(self):
        """/shop renders the roots, marks them lazy, and skips their children."""
        body = self.url_open("/shop").text

        self.assertIn("TB Root Category", body, "the root category must still be listed")
        self.assertIn(
            f'data-lazy-category="{self.root.id}"',
            body,
            "the collapsed root branch must advertise the id to fetch",
        )
        self.assertNotIn(
            "TB Child Category",
            body,
            "a collapsed branch must not ship its children — that is the whole point",
        )
        self.assertNotIn("TB Grandchild Category", body)

    def test_category_page_renders_open_branch(self):
        """On a category page the branch leading to it is rendered server-side."""
        slug = self.env["ir.http"]._slug(self.grandchild)
        body = self.url_open(f"/shop/category/{slug}").text

        self.assertIn("TB Root Category", body)
        self.assertIn("TB Child Category", body, "the open branch must be rendered")
        self.assertIn("TB Grandchild Category", body)

    def test_children_endpoint_returns_branch(self):
        """The endpoint returns the direct children, and only those."""
        response = self.url_open(f"/shop/category_children/{self.root.id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("TB Child Category", response.text)
        # Grandchildren belong to the next expand, not this one.
        self.assertNotIn("TB Grandchild Category", response.text)

    def test_children_endpoint_keeps_query_state(self):
        """Filters of the calling page survive into the fetched links."""
        response = self.url_open(f"/shop/category_children/{self.root.id}?order=list_price+desc")

        self.assertEqual(response.status_code, 200)
        self.assertIn("order=list_price", response.text)

    def test_children_endpoint_without_children(self):
        """A leaf yields an empty body rather than an error."""
        response = self.url_open(f"/shop/category_children/{self.grandchild.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")

    def test_children_endpoint_unknown_category(self):
        """An unknown id is a 404, not an empty success."""
        response = self.url_open("/shop/category_children/999999999")

        self.assertEqual(response.status_code, 404)

    def test_search_keeps_tree_fully_rendered(self):
        """While searching, the (already filtered) tree stays server-rendered.

        The search narrows the tree to matching categories, so it is small; not
        lazy-loading it keeps the search behaviour identical to before.
        """
        body = self.url_open("/shop?search=TB+Lazy+Product").text

        self.assertIn("TB Child Category", body)
        self.assertNotIn("data-lazy-category", body)
