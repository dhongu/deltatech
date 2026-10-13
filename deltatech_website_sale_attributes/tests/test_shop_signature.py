# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install")
class TestShopSignature(HttpCase):
    """``?ppg=`` must never filter the shop by price.

    This override used to declare ``shop(self, page, category, search, ppg)``
    and forward those four positionally. Core's fourth parameter is
    ``min_price``, so ``?ppg=40`` reached it as ``min_price=40`` and dropped
    every product cheaper than that from the listing, silently. On 19.0 ``ppg``
    is not a core parameter at all, which makes the old signature worse rather
    than better: it captured a value core would otherwise have ignored and
    pushed it into the price filter.

    Assertions run against a category created here. These tests are
    ``post_install``, so the global listing holds an unknown number of
    published products and a single test product can land on page two — and on
    19.0 ``?ppg=`` cannot widen the page to compensate.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.category = cls.env["product.public.category"].create({"name": "TB Signature Category"})
        cls.cheap = cls.env["product.template"].create(
            {
                "name": "TB Signature Cheap Product",
                "is_published": True,
                "list_price": 5.0,
                "public_categ_ids": [(6, 0, cls.category.ids)],
            }
        )
        cls.category_url = f"/shop/category/{cls.env['ir.http']._slug(cls.category)}"

    def test_ppg_does_not_filter_by_price(self):
        """A product below the ``ppg`` value must still be listed."""
        body = self.url_open(f"{self.category_url}?ppg=40").text

        self.assertIn(
            self.cheap.name,
            body,
            "a 5.0 product disappeared under ?ppg=40 — ppg is being read as min_price",
        )

    def test_min_price_still_filters(self):
        """The real ``min_price`` parameter must keep working.

        Without this the fix could have passed by disabling price filtering
        altogether.
        """
        body = self.url_open(f"{self.category_url}?min_price=40").text

        self.assertNotIn(
            self.cheap.name,
            body,
            "min_price=40 should have excluded a 5.0 product",
        )
