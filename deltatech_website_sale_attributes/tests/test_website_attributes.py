# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install")
class TestStockWebsiteAAttribute(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        current_website = cls.env["website"].get_current_website()
        cls.current_website = current_website

        # Test data: one attribute with two values (one visible, one hidden), and a product using both
        ProductTemplate = cls.env["product.template"]
        ProductAttribute = cls.env["product.attribute"]
        ProductAttributeValue = cls.env["product.attribute.value"]

        cls.attribute = ProductAttribute.create({
            "name": "Test Attr",
            # using 'no_variant' keeps a single template variant; easier for tests
            "create_variant": "no_variant",
        })
        cls.value_visible = ProductAttributeValue.create({
            "name": "Visible",
            "attribute_id": cls.attribute.id,
            "visibility": "visible",
        })
        cls.value_hidden = ProductAttributeValue.create({
            "name": "Hidden",
            "attribute_id": cls.attribute.id,
            "visibility": "hidden",
        })

        cls.product = ProductTemplate.create({
            "name": "Test Product",
            "attribute_line_ids": [
                (
                    0,
                    0,
                    {
                        "attribute_id": cls.attribute.id,
                        "value_ids": [(6, 0, [cls.value_visible.id, cls.value_hidden.id])],
                    },
                )
            ],
        })

        # Fetch the generated product.template.attribute.value records (v17-safe)
        ptavs = cls.env["product.template.attribute.value"].search([
            ("product_tmpl_id", "=", cls.product.id),
        ])
        cls.ptav_visible = ptavs.filtered(
            lambda r: r.product_attribute_value_id.id == cls.value_visible.id
        )
        cls.ptav_hidden = ptavs.filtered(
            lambda r: r.product_attribute_value_id.id == cls.value_hidden.id
        )

    def test_call_shop(self):
        # Basic smoke test: the shop page should load
        resp = self.url_open("/shop")
        self.assertTrue(resp, "Expected a response when opening /shop")

    def test_website_visible_flag_computed(self):
        # Ensure the computed field reflects the underlying value visibility
        self.assertTrue(
            self.ptav_visible.website_visible,
            "PTAV linked to a visible value should have website_visible = True",
        )
        self.assertFalse(
            self.ptav_hidden.website_visible,
            "PTAV linked to a hidden value should have website_visible = False",
        )

    def test_only_active_filters_by_website_visibility(self):
        # The helper should keep only visible ones when a website_id is present in context
        recs = self.ptav_visible | self.ptav_hidden
        filtered = recs.with_context(website_id=self.current_website.id)._only_active()
        self.assertIn(self.ptav_visible, filtered, "Visible PTAV should remain after _only_active()")
        self.assertNotIn(self.ptav_hidden, filtered, "Hidden PTAV should be filtered out by _only_active()")
