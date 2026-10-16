# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import re

from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase


@tagged("post_install", "-at_install")
class TestProductCodeVariants(HttpCase):
    """#3493: /shop/product-code/<code> resolves the codes of the variants."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute = cls.env["product.attribute"].create(
            {
                "name": "WPC Color",
                "create_variant": "always",
                "value_ids": [(0, 0, {"name": "Red"}), (0, 0, {"name": "Blue"})],
            }
        )
        red, blue = cls.attribute.value_ids
        cls.template = cls.env["product.template"].create(
            {
                "name": "WPC Multi Variant",
                "type": "consu",
                "is_published": True,
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": cls.attribute.id, "value_ids": [(6, 0, [red.id, blue.id])]})
                ],
            }
        )
        cls.variants = {}
        for variant in cls.template.product_variant_ids:
            color = variant.product_template_attribute_value_ids.product_attribute_value_id
            code = "WPCRED01" if color == red else "WPCBLUE01"
            variant.default_code = code
            cls.variants[code] = variant
        cls.unpublished = cls.env["product.template"].create(
            {
                "name": "WPC Hidden Variant",
                "type": "consu",
                "is_published": False,
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": cls.attribute.id, "value_ids": [(6, 0, [red.id, blue.id])]})
                ],
            }
        )
        cls.unpublished.product_variant_ids[0].default_code = "WPCHIDDEN01"

    def _selected_variant_id(self, response):
        match = re.search(r'name="product_id"[^>]*value="(\d+)"', response.text) or re.search(
            r'value="(\d+)"[^>]*name="product_id"', response.text
        )
        return match and int(match.group(1))

    def test_variant_codes_open_the_template_with_that_variant(self):
        self.assertFalse(self.template.default_code)
        for code, variant in self.variants.items():
            response = self.url_open(f"/shop/product-code/{code}")
            self.assertEqual(response.status_code, 200, code)
            self.assertEqual(self._selected_variant_id(response), variant.id, code)

    def test_unpublished_variant_code_is_not_found(self):
        response = self.url_open("/shop/product-code/WPCHIDDEN01")
        self.assertEqual(response.status_code, 404)


@tagged("post_install", "-at_install")
class TestMultiCodeSearchComplete(TransactionCase):
    """#3494: the pasted-code search counts and ranks the complete set of matches."""

    def test_more_matches_than_the_old_branch_cap(self):
        products = self.env["product.template"].create(
            [{"name": f"WPCMULTI{i:04d}", "type": "consu"} for i in range(520)]
        )
        search_detail = {"base_domain": [[("id", "in", products.ids)]], "search_fields": ["name"]}
        ProductTemplate = self.env["product.template"]
        results, count = ProductTemplate._search_fetch_multi_code(search_detail, ["WPCMULTI"], 20, "id desc")
        self.assertEqual(count, 520)
        # The highest id ranks first in this order, although it is past the first 500 ids
        self.assertEqual(results[0], products[-1])
        self.assertEqual(len(results), 20)


@tagged("post_install", "-at_install")
class TestLegacyMinTermLength(TransactionCase):
    """#3495: a non-numeric minimum term length does not break the shop search."""

    def test_legacy_false_value_disables_the_filter(self):
        ProductTemplate = self.env["product.template"]
        for value in ("False", "abc"):
            self.env["ir.config_parameter"].sudo().set_param("website_search.min_term_length", value)
            # Must not raise
            ProductTemplate._search_build_domain([[]], "ab cdef", ["name"])
            self.assertEqual(ProductTemplate._min_term_length(), 0, value)

    def test_numeric_value_is_used(self):
        self.env["ir.config_parameter"].sudo().set_param("website_search.min_term_length", "4")
        self.assertEqual(self.env["product.template"]._min_term_length(), 4)
