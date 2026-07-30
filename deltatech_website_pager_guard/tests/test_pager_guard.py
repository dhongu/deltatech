# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestPagerGuard(HttpCase):
    """Shop pages past the last real one must 404, not serve duplicate content.

    Page-count assertions run against a category created here, never against
    ``/shop`` as a whole. These tests are ``post_install``, so every other
    addon's fixtures are already committed and the global listing holds an
    unknown number of published products — CI proved it by serving
    ``/shop/page/4`` where a local database had only three pages.

    Page size comes from ``website.shop_ppg`` rather than a ``?ppg=`` query
    parameter. That parameter is unreliable once other addons override
    ``shop()``: some forward it positionally into core's ``min_price``, which
    leaves the page size untouched *and* filters the catalogue by price.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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
        cls.category_url = f"/shop/category/{cls.env['ir.http']._slug(cls.category)}"

    def test_shop_first_page_is_served(self):
        """/shop and /shop/page/1 are valid whatever the catalogue holds."""
        self.assertEqual(self.url_open("/shop").status_code, 200)
        self.assertEqual(self.url_open("/shop/page/1").status_code, 200)

    def test_absurd_page_is_refused(self):
        """The page number seen in production crawler logs is refused.

        Safe to assert on the global listing: no catalogue reaches three
        million pages.
        """
        self.assertEqual(self.url_open("/shop/page/3467514").status_code, 404)

    def test_last_real_page_is_served(self):
        """Three products at one per page make page 3 the last real one.

        Also proves ``shop_ppg`` took effect: at the default page size the
        three products would share page 1 and page 3 would 404.
        """
        self.assertEqual(self.url_open(f"{self.category_url}/page/2").status_code, 200)
        self.assertEqual(self.url_open(f"{self.category_url}/page/3").status_code, 200)

    def test_page_beyond_last_is_refused(self):
        """Page 4 does not exist and must 404 instead of being clamped to 3."""
        self.assertEqual(self.url_open(f"{self.category_url}/page/4").status_code, 404)

    def test_guard_uses_page_count_not_a_fixed_bound(self):
        """The refusal follows the real page count, not a hardcoded ceiling.

        A live catalogue was measured at 2.578 shop pages, so any constant
        bound would refuse real pages. Here the boundary sits exactly between
        page 3 and page 4, which only a ``page_count`` comparison can place.
        """
        self.assertEqual(self.url_open(f"{self.category_url}/page/3").status_code, 200)
        self.assertEqual(self.url_open(f"{self.category_url}/page/4").status_code, 404)

    def test_empty_category_has_no_second_page(self):
        """With no product at all the pager reports zero pages; page 2 must 404."""
        empty = self.env["product.public.category"].create({"name": "TB Empty Category"})
        slug = self.env["ir.http"]._slug(empty)

        self.assertEqual(self.url_open(f"/shop/category/{slug}").status_code, 200)
        self.assertEqual(self.url_open(f"/shop/category/{slug}/page/2").status_code, 404)
