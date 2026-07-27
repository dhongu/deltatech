# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestExactPhraseSearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].get_current_website()
        cls.ProductTemplate = cls.env["product.template"]
        cls.set_param = cls.env["ir.config_parameter"].sudo().set_param

        # The wanted product: its code contains spaces, as OEM part numbers do.
        cls.exact_product = cls._create_product("Bucsa ZQX", "ZQX 100 200 300")
        # Noise: every term of the code above appears in the name, but not as a
        # single string, so only the per-term search can match it.
        cls.noise_product = cls._create_product("Suport ZQX 100 sau 200 ori 300", "ZQXNOISE")

    @classmethod
    def _create_product(cls, name, default_code):
        return cls.ProductTemplate.create(
            {
                "name": name,
                "default_code": default_code,
                "is_published": True,
                "website_sequence": 1,
            }
        )

    def _search(self, search, limit=20):
        # Same options the shop controller passes, so that modules adjusting
        # search_fields for the optional fields are exercised as in production.
        options = {
            "displayImage": True,
            "displayDescription": True,
            "displayExtraLink": True,
            "displayDetail": True,
            "display_currency": self.website.currency_id,
        }
        search_detail = self.ProductTemplate._search_get_detail(self.website, None, options)
        results, _count = self.ProductTemplate._search_fetch(search_detail, search, limit, None)
        return results

    def test_disabled_by_default_splits_the_term(self):
        results = self._search("ZQX 100 200 300")
        self.assertIn(self.exact_product, results)
        self.assertIn(self.noise_product, results, "without exact phrase search the term is split per word")

    def test_exact_phrase_returns_only_the_matching_code(self):
        self.set_param("website_search.exact_phrase", "True")
        results = self._search("ZQX 100 200 300")
        self.assertEqual(results, self.exact_product)

    def test_exact_phrase_ignores_extra_whitespace(self):
        self.set_param("website_search.exact_phrase", "True")
        results = self._search("  ZQX   100 200  300 ")
        self.assertEqual(results, self.exact_product)

    def test_exact_phrase_matches_a_code_inside_a_longer_value(self):
        # Alternative codes are often kept several per line; the searched code
        # is then a substring of the stored value.
        product = self._create_product("Bucsa ZQW", "ZQW 11 22 MERCEDES ZQW 33 44 MERCEDES")
        self.set_param("website_search.exact_phrase", "True")
        self.assertEqual(self._search("ZQW 33 44"), product)

    def test_exact_phrase_falls_back_when_the_phrase_has_no_match(self):
        self.set_param("website_search.exact_phrase", "True")
        # No product contains "ZQX 300 100" as a single string, so the search
        # degrades to the per-term behaviour instead of returning nothing.
        results = self._search("ZQX 300 100")
        self.assertIn(self.exact_product, results)
        self.assertIn(self.noise_product, results)

    def test_exact_phrase_does_not_or_expand_a_missing_code(self):
        # "100 200 300 999" looks like four pasted codes to the multi-code fast
        # path, which would OR them and return every product containing any one
        # group - the very noise exact-phrase search exists to remove. In this
        # mode a spaced term is one code, so a missing code returns nothing
        # rather than an OR expansion.
        self.set_param("website_search.exact_phrase", "True")
        self.assertFalse(self._search("100 200 300 999"))

    def test_pasted_code_lists_still_work_when_exact_phrase_is_off(self):
        codes = ["ZQY111111", "ZQY222222", "ZQY333333", "ZQY444444"]
        products = self.ProductTemplate.browse()
        for code in codes[:2]:
            products |= self._create_product(f"Rulment {code}", code)
        # Default configuration: the multi-code fast path resolves the list.
        self.assertEqual(self._search(" ".join(codes)), products)

    def test_pasted_code_lists_are_not_or_expanded_with_exact_phrase(self):
        codes = ["ZQY111111", "ZQY222222", "ZQY333333", "ZQY444444"]
        for code in codes[:2]:
            self._create_product(f"Rulment {code}", code)
        self.set_param("website_search.exact_phrase", "True")
        # No product carries all four codes, and the OR path is off in this
        # mode, so the list resolves to nothing.
        self.assertFalse(self._search(" ".join(codes)))

    def test_single_term_search_is_unaffected(self):
        self.set_param("website_search.exact_phrase", "True")
        self.assertEqual(self._search("ZQXNOISE"), self.noise_product)
