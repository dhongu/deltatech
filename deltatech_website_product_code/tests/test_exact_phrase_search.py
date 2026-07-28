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
                "type": "consu",
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

    def test_a_search_of_words_only_is_never_matched_as_a_phrase(self):
        # A term without digits describes a product rather than quoting a code.
        # Matching it as one string would drop the products whose words are
        # spread out, which is not what the shopper means.
        spread = self._create_product("Lant combina agricola ZQCLAAS", "ZQL001")
        literal = self._create_product("Lant ZQCLAAS", "ZQL002")
        self.set_param("website_search.exact_phrase", "True")
        results = self._search("Lant ZQCLAAS")
        self.assertIn(literal, results)
        self.assertIn(spread, results, "words are searched separately when the term has no digit")

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
        # "100 200 300 999" is one code written in groups, not four pasted
        # codes. Without the standalone-code test the multi-code fast path would
        # OR the groups and return every product containing any one of them -
        # the very noise exact-phrase search exists to remove.
        self.set_param("website_search.exact_phrase", "True")
        self.assertFalse(self._search("100 200 300 999"))

    def test_exact_phrase_treats_four_character_groups_as_one_code(self):
        # Boundary of website_search.standalone_code_min_length (5): groups of
        # four characters still belong to a single code.
        self.set_param("website_search.exact_phrase", "True")
        self.assertFalse(self._search("1000 2000 3000 9999"))

    def test_pasted_code_lists_still_work_when_exact_phrase_is_off(self):
        codes = ["ZQY111111", "ZQY222222", "ZQY333333", "ZQY444444"]
        products = self.ProductTemplate.browse()
        for code in codes[:2]:
            products |= self._create_product(f"Rulment {code}", code)
        # Default configuration: the multi-code fast path resolves the list.
        self.assertEqual(self._search(" ".join(codes)), products)

    def test_pasted_code_lists_still_work_with_exact_phrase(self):
        codes = ["ZQY111111", "ZQY222222", "ZQY333333", "ZQY444444"]
        products = self.ProductTemplate.browse()
        for code in codes[:2]:
            products |= self._create_product(f"Rulment {code}", code)
        self.set_param("website_search.exact_phrase", "True")
        # Each term is long enough to be a code of its own, so the list is
        # resolved by the multi-code fast path even in exact-phrase mode.
        self.assertEqual(self._search(" ".join(codes)), products)

    def test_terms_shorter_than_the_minimum_are_dropped(self):
        product = self._create_product("Rulment ZQZ12345", "ZQZ12345")
        # "ab" is shorter than website_search.min_term_length (3). Terms are
        # ANDed, so without dropping it the product could not be found.
        self.assertIn(product, self._search("ZQZ12345 ab"))

    def test_a_search_made_only_of_short_terms_is_kept(self):
        product = self._create_product("Set ab cd", "ZQZSHORT")
        # Every term is short, so the search is kept intact rather than emptied.
        self.assertIn(product, self._search("ab cd"))

    def test_single_term_search_is_unaffected(self):
        self.set_param("website_search.exact_phrase", "True")
        self.assertEqual(self._search("ZQXNOISE"), self.noise_product)
