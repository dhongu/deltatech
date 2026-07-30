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

        Three products with ``ppg=1`` give exactly three pages, so page 4 is the
        first one that does not exist.
        """
        self.assertEqual(self.url_open("/shop/page/3?ppg=1").status_code, 200)
        self.assertEqual(self.url_open("/shop/page/4?ppg=1").status_code, 404)

    def test_absurd_page_is_refused(self):
        """The page number seen in production crawler logs is refused."""
        self.assertEqual(self.url_open("/shop/page/3467514").status_code, 404)

    def test_guard_uses_page_count_not_a_fixed_bound(self):
        """A high but real page number must still be served.

        The guard compares against the pager's own ``page_count``; a hardcoded
        ceiling would refuse real pages, and a live catalogue was measured at
        2.578 shop pages. With ``ppg=1`` and three products, page 3 is both the
        last real page and proof that the check is not off by one.
        """
        self.assertEqual(self.url_open("/shop/page/3?ppg=1").status_code, 200)
        self.assertEqual(self.url_open("/shop/page/2?ppg=1").status_code, 200)

    def test_category_page_beyond_last_is_refused(self):
        """The guard applies to category listings too, not only to /shop."""
        slug = self.env["ir.http"]._slug(self.category)

        self.assertEqual(self.url_open(f"/shop/category/{slug}").status_code, 200)
        self.assertEqual(self.url_open(f"/shop/category/{slug}/page/4?ppg=1").status_code, 404)

    def test_empty_category_has_no_second_page(self):
        """With no product at all the pager reports zero pages; page 2 must 404."""
        empty = self.env["product.public.category"].create({"name": "TB Empty Category"})
        slug = self.env["ir.http"]._slug(empty)

        self.assertEqual(self.url_open(f"/shop/category/{slug}").status_code, 200)
        self.assertEqual(self.url_open(f"/shop/category/{slug}/page/2").status_code, 404)
