# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSearchGetDetail(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].get_current_website()
        cls.ProductTemplate = cls.env["product.template"]

    def _search_detail(self, display_description):
        # Same options the search bar snippet posts to
        # /website/snippet/autocomplete, where every display option can be
        # turned off from the website editor.
        options = {
            "displayImage": True,
            "displayDescription": display_description,
            "displayExtraLink": True,
            "displayDetail": True,
            "display_currency": self.website.currency_id,
        }
        return self.ProductTemplate._search_get_detail(self.website, None, options)

    def test_alternative_code_is_searchable(self):
        detail = self._search_detail(True)
        self.assertIn("alternative_ids.name", detail["search_fields"])
        self.assertIn("alternative_ids.name", detail["mapping"])

    def test_description_is_dropped_when_displayed(self):
        detail = self._search_detail(True)
        self.assertNotIn("description", detail["search_fields"])
        self.assertNotIn("description_sale", detail["search_fields"])

    def test_description_not_displayed(self):
        # website_sale does not add the description fields at all in this case,
        # so removing them must not raise.
        detail = self._search_detail(False)
        self.assertNotIn("description", detail["search_fields"])
        self.assertNotIn("description_sale", detail["search_fields"])
        self.assertIn("alternative_ids.name", detail["search_fields"])
