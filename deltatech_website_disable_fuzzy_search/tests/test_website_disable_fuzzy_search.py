from unittest.mock import patch

from odoo.tests.common import TransactionCase

from ..controllers.main import Website, WebsiteSale


class TestWebsiteDisableFuzzySearch(TransactionCase):
    def test_01_search_options_fuzzy_disabled(self):
        """Test if _get_search_options sets allowFuzzy to False"""
        controller = WebsiteSale()
        # Mock super()._get_search_options to return a dict with allowFuzzy=True
        # We target the specific class we expect super() to call
        with patch(
            "odoo.addons.website_sale.controllers.main.WebsiteSale._get_search_options",
            return_value={"allowFuzzy": True},
        ):
            options = controller._get_search_options()
            self.assertFalse(options.get("allowFuzzy"), "Fuzzy search should be disabled in search options")

    def test_02_autocomplete_fuzzy_disabled(self):
        """Test if autocomplete sets allowFuzzy to False in options"""
        controller = Website()

        # The error occurred because autocomplete is decorated with @http.route()
        # Calling it directly might trigger Odoo's routing logic which expects a request context.
        # We can try to mock the super call without actually triggering the route logic if possible,
        # or just mock the Website.autocomplete itself.

        # To avoid KeyError: 'type' from route_wrapper, we can call the original function directly
        # bypass the decorator if possible, but in Odoo it's tricky.
        # Alternatively, we can use the __wrapped__ attribute if it's a standard decorator.

        func = Website.autocomplete
        if hasattr(func, "__wrapped__"):
            func = func.__wrapped__

        with patch("odoo.addons.website_sale.controllers.website.Website.autocomplete") as mock_autocomplete:
            # Call the function directly, passing self as controller
            func(controller, term="test")

            # Check the last argument (options) of the call to super().autocomplete
            args, kwargs = mock_autocomplete.call_args
            # autocomplete(self, search_type, term, order, limit, max_nb_chars, options)
            options = args[5] if len(args) > 5 else kwargs.get("options")
            self.assertFalse(options.get("allowFuzzy"), "Fuzzy search should be disabled in autocomplete options")
