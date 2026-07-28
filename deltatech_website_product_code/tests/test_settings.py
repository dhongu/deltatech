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

    def test_default_matches_the_value_read_by_the_search(self):
        # Saving the settings page writes every field, so a default that
        # differed from what the search assumes would silently change the
        # behaviour of a shop where nobody touched this setting.
        settings = self.Settings.create({})
        self.assertFalse(settings.website_search_exact_phrase)
        settings.execute()
        self.assertFalse(self.ProductTemplate._exact_phrase_search_enabled())

    def test_enabling_exact_phrase_from_the_settings(self):
        settings = self.Settings.create({"website_search_exact_phrase": True})
        settings.execute()
        self.assertTrue(self.ProductTemplate._exact_phrase_search_enabled())

    def test_disabling_exact_phrase_from_the_settings(self):
        self.env["ir.config_parameter"].sudo().set_param("website_search.exact_phrase", "True")
        settings = self.Settings.create({})
        self.assertTrue(settings.website_search_exact_phrase)
        settings.website_search_exact_phrase = False
        settings.execute()
        self.assertFalse(self.ProductTemplate._exact_phrase_search_enabled())
