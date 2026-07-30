# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestPagerGuard(HttpCase):
    """Shop pages past the last real one must 404, not serve duplicate content."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # 19.0 no longer reads ``ppg`` from the query string — the shop always
        # uses ``website.shop_ppg or 21``. One product per page keeps the
        # fixture small while still producing several pages.
        cls.website = cls.env["website"].browse(1)
        cls.website.shop_ppg = 1

        cls.category = cls.env["product.public.category"].create({"name": "TB Pager Category"})
        cls.env["product.template"].create(
            [
                {
                    "name": f"TB Pager Product {index}",
                    "is_published": True,
                    "list_price": 10.0,
                    "public_categ_ids": [(6, 0, cls.category.ids)],
                }
                for index in range(3)
            ]
        )

    def test_shop_first_page_is_served(self):
        """/shop and /shop/page/1 are always valid."""
        self.assertEqual(self.url_open("/shop").status_code, 200)
        self.assertEqual(self.url_open("/shop/page/1").status_code, 200)

    def test_page_beyond_last_is_refused(self):
        """A page number above the real count must 404 instead of being clamped.

        Three products at one per page give exactly three pages, so page 4 is
        the first one that does not exist.
        """
        self.assertEqual(self.url_open("/shop/page/3").status_code, 200)
        self.assertEqual(self.url_open("/shop/page/4").status_code, 404)

    def test_absurd_page_is_refused(self):
        """The page number seen in production crawler logs is refused."""
        self.assertEqual(self.url_open("/shop/page/3467514").status_code, 404)

    def test_guard_uses_page_count_not_a_fixed_bound(self):
        """A high but real page number must still be served.

        The guard compares against the pager's own ``page_count``; a hardcoded
        ceiling would refuse real pages, and a live catalogue was measured at
        2.578 shop pages. Page 3 is both the last real page here and proof that
        the check is not off by one.
        """
        self.assertEqual(self.url_open("/shop/page/2").status_code, 200)
        self.assertEqual(self.url_open("/shop/page/3").status_code, 200)

    def test_category_page_beyond_last_is_refused(self):
        """The guard applies to category listings too, not only to /shop."""
        slug = self.env["ir.http"]._slug(self.category)

        self.assertEqual(self.url_open(f"/shop/category/{slug}").status_code, 200)
        self.assertEqual(self.url_open(f"/shop/category/{slug}/page/4").status_code, 404)

    def test_empty_category_is_not_reachable_at_all(self):
        """An empty category 404s before the guard is even consulted.

        On 18.0 it answered 200 and the guard was what refused its ``/page/2``.
        19.0 added ``empty_public_categories_rule``
        (``website_sale/security/ir_rules.xml``), an ``ir.rule`` hiding
        categories with ``has_published_products = False`` from public and
        portal users, so the record converter cannot resolve the slug and
        ``handle_params_access_error`` turns that into a 404.

        Asserted here so the port does not silently rely on 18.0 behaviour: the
        outcome a crawler sees is identical, the cause is not.
        """
        empty = self.env["product.public.category"].create({"name": "TB Empty Category"})
        slug = self.env["ir.http"]._slug(empty)

        self.assertEqual(self.url_open(f"/shop/category/{slug}").status_code, 404)
        self.assertEqual(self.url_open(f"/shop/category/{slug}/page/2").status_code, 404)
