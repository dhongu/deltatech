# © 2008-2026 Deltatech / Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, tagged

STYLES = ("dot", "theme", "outline", "bar", "status")


@tagged("post_install", "-at_install")
class TestStockBadgeStyle(HttpCase):
    """The stock badge style picked in the website builder is a view adding its class on #product_detail."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.template"].create(
            {"name": "Stock badge product", "is_storable": True, "is_published": True, "list_price": 10}
        )

    def _product_detail_classes(self):
        response = self.url_open(self.product.website_url)
        self.assertEqual(response.status_code, 200)
        start = response.text.index('id="product_detail"')
        section = response.text[response.text.rindex("<section", 0, start) : response.text.index(">", start)]
        return section

    def test_styles_inactive_by_default(self):
        for style in STYLES:
            view = self.env.ref(f"deltatech_website_stock_availability.product_stock_badge_{style}")
            self.assertFalse(view.active, style)
        section = self._product_detail_classes()
        self.assertNotIn("o_wsale_stock_badge_", section)

    def test_style_view_adds_class(self):
        views = {s: self.env.ref(f"deltatech_website_stock_availability.product_stock_badge_{s}") for s in STYLES}
        for style in STYLES:
            for view in views.values():
                view.active = False
            views[style].active = True
            section = self._product_detail_classes()
            self.assertIn(f"o_wsale_stock_badge_{style}", section)
            for other in set(STYLES) - {style}:
                self.assertNotIn(f"o_wsale_stock_badge_{other}", section)
