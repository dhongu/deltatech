# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install")
class TestShopSignature(HttpCase):
    """``?ppg=`` must page the shop, never filter it by price.

    This override used to declare ``shop(self, page, category, search, ppg)``
    and forward those four positionally. Core's fourth parameter is
    ``min_price``, so ``?ppg=40`` reached it as ``min_price=40`` and dropped
    every product cheaper than that from the listing, silently, while the page
    size stayed at its default.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.website = cls.env["website"].get_current_website()
        cls.cheap = cls.env["product.template"].create(
            {
                "name": "TB Signature Cheap Product",
                "is_published": True,
                "list_price": 5.0,
            }
        )

    def test_ppg_does_not_filter_by_price(self):
        """A product below the ``ppg`` value must still be listed."""
        body = self.url_open("/shop?ppg=40").text

        self.assertIn(
            self.cheap.name,
            body,
            "a 5.0 product disappeared from /shop?ppg=40 — ppg is being read as min_price",
        )

    def test_min_price_still_filters(self):
        """The real ``min_price`` parameter must keep working."""
        body = self.url_open("/shop?min_price=40").text

        self.assertNotIn(
            self.cheap.name,
            body,
            "min_price=40 should have excluded a 5.0 product",
        )
