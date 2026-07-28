# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSearchSettings(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Settings = self.env["res.config.settings"]
        self.ProductTemplate = self.env["product.template"]
        self.get_param = self.env["ir.config_parameter"].sudo().get_param

    def test_defaults_match_the_values_read_by_the_search(self):
        # Saving the settings page writes every field, so a default that differs
        # from what the search assumes would silently change the behaviour of a
        # shop where nobody touched these settings.
        settings = self.Settings.create({})
        self.assertFalse(settings.website_search_exact_phrase)
        self.assertEqual(settings.website_search_standalone_code_min_length, 5)
        self.assertEqual(settings.website_search_multi_code_min_terms, 4)
        self.assertEqual(settings.website_search_min_term_length, 3)

        settings.execute()

        self.assertFalse(self.ProductTemplate._exact_phrase_search_enabled())
        self.assertEqual(self.ProductTemplate._standalone_code_min_length(), 5)
        self.assertEqual(self.ProductTemplate._multi_code_min_terms(), 4)
        self.assertEqual(int(self.get_param("website_search.min_term_length")), 3)

    def test_enabling_exact_phrase_from_the_settings(self):
        settings = self.Settings.create({"website_search_exact_phrase": True})
        settings.execute()
        self.assertTrue(self.ProductTemplate._exact_phrase_search_enabled())

    def test_zero_standalone_length_accepts_any_term(self):
        settings = self.Settings.create(
            {"website_search_exact_phrase": True, "website_search_standalone_code_min_length": 0}
        )
        settings.execute()
        self.assertEqual(self.ProductTemplate._standalone_code_min_length(), 0)
        self.assertTrue(self.ProductTemplate._looks_like_standalone_code("366"))

    def test_short_terms_are_not_standalone_codes_by_default(self):
        self.assertFalse(self.ProductTemplate._looks_like_standalone_code("366"))
        self.assertTrue(self.ProductTemplate._looks_like_standalone_code("FLO10229"))

    def test_a_disabled_fast_path_survives_saving_the_settings(self):
        # Zero must be written out, not turned into a missing parameter: the
        # settings page would otherwise silently restore the default of 4 and
        # re-enable a fast path the customer had deliberately switched off.
        self.env["ir.config_parameter"].sudo().set_param("website_search.multi_code_min_terms", "0")
        settings = self.Settings.create({})
        self.assertEqual(settings.website_search_multi_code_min_terms, 0)
        settings.execute()
        self.assertEqual(self.get_param("website_search.multi_code_min_terms"), "0")
        self.assertEqual(self.ProductTemplate._multi_code_min_terms(), 0)

    def test_legacy_false_value_is_read_as_disabled(self):
        self.env["ir.config_parameter"].sudo().set_param("website_search.multi_code_min_terms", "False")
        self.assertEqual(self.Settings.create({}).website_search_multi_code_min_terms, 0)
