# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
"""The locality list offered at checkout follows the carrier's own catalog.

The carrier modules are not a dependency here -- what this module knows is the
seam, ``delivery.carrier._get_city_domain()``. So the tests stand in for a
carrier catalog by patching that method, which is exactly what DPD, Sameday,
Cargus and Fan Curier implement on their side.
"""

import json
import re
from unittest.mock import patch

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestCarrierCityFilter(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env["res.country"].create(
            {"name": "Carrierland", "code": "XC", "enforce_cities": True, "state_required": True}
        )
        cls.state = cls.env["res.country.state"].create(
            {"name": "Served County", "code": "SC", "country_id": cls.country.id}
        )
        # A county the carrier knows nothing about, to cover the fallback.
        cls.other_state = cls.env["res.country.state"].create(
            {"name": "Unknown County", "code": "UC", "country_id": cls.country.id}
        )
        cls.served_city, cls.unserved_city = cls.env["res.city"].create(
            [
                {"name": "Served City", "state_id": cls.state.id, "country_id": cls.country.id, "zipcode": "10000"},
                {"name": "Unserved City", "state_id": cls.state.id, "country_id": cls.country.id, "zipcode": "10001"},
            ]
        )
        cls.other_city = cls.env["res.city"].create(
            {"name": "Far City", "state_id": cls.other_state.id, "country_id": cls.country.id}
        )

        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "fixed",
                "fixed_price": 10.0,
                "product_id": cls.env["product.product"].create({"name": "Test Delivery", "type": "service"}).id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "list_price": 100.0, "sale_ok": True, "website_published": True}
        )

    def _fill_cart(self):
        """Create a cart for the anonymous session and return it."""
        self._rpc("/shop/cart/update_json", {"product_id": self.product.id, "add_qty": 1})
        order = self.env["sale.order"].search([("website_id", "!=", False)], order="id desc", limit=1)
        self.assertTrue(order, "the cart was not created")
        return order

    def _rpc(self, url, params=None):
        response = self.url_open(
            url,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params or {}}),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
        self.assertNotIn("error", payload, payload.get("error"))
        return payload["result"]

    def _csrf_token(self, url):
        """The form posts one, and the request is refused without it."""
        page = self.url_open(url)
        page.raise_for_status()
        match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text)
        self.assertTrue(match, "no csrf token on the address page")
        return match.group(1)

    def _city_names(self, state, **params):
        result = self._rpc(f"/shop/state_infos/{state.id}", params)
        return {city[1] for city in result["cities"]}

    def _catalog(self, cities):
        """Stand in for a carrier that knows exactly these localities."""
        return patch.object(
            type(self.env["delivery.carrier"]),
            "_get_city_domain",
            lambda carrier: [("id", "in", cities.ids)],
            create=True,
        )

    def test_delivery_address_offers_only_the_localities_the_carrier_serves(self):
        self._fill_cart().carrier_id = self.carrier
        with self._catalog(self.served_city):
            names = self._city_names(self.state, address_type="delivery")
        self.assertEqual(names, {self.served_city.display_name})

    def test_billing_address_is_not_restricted_by_the_carrier(self):
        """Where the parcel is billed is no business of the courier."""
        self._fill_cart().carrier_id = self.carrier
        with self._catalog(self.served_city):
            names = self._city_names(self.state, address_type="billing")
        self.assertEqual(names, {self.served_city.display_name, self.unserved_city.display_name})

    def test_billing_address_used_as_delivery_is_restricted(self):
        self._fill_cart().carrier_id = self.carrier
        with self._catalog(self.served_city):
            names = self._city_names(self.state, address_type="billing", use_delivery_as_billing="True")
        self.assertEqual(names, {self.served_city.display_name})

    def test_no_carrier_chosen_yet_leaves_the_list_whole(self):
        """The address page is reached before the delivery step."""
        self._fill_cart()
        with self._catalog(self.served_city):
            names = self._city_names(self.state, address_type="delivery")
        self.assertEqual(names, {self.served_city.display_name, self.unserved_city.display_name})

    def test_a_county_the_carrier_does_not_cover_leaves_the_list_whole(self):
        """Rather than hand the customer an empty dropdown."""
        self._fill_cart().carrier_id = self.carrier
        with self._catalog(self.served_city):
            names = self._city_names(self.other_state, address_type="delivery")
        self.assertEqual(names, {self.other_city.display_name})

    def test_a_carrier_without_a_catalog_leaves_the_list_whole(self):
        """Packeta and the like ship anywhere: an empty domain, and no filter."""
        self._fill_cart().carrier_id = self.carrier
        no_catalog = patch.object(
            type(self.env["delivery.carrier"]), "_get_city_domain", lambda carrier: [], create=True
        )
        with no_catalog:
            names = self._city_names(self.state, address_type="delivery")
        self.assertEqual(names, {self.served_city.display_name, self.unserved_city.display_name})

    def test_a_locality_outside_the_catalog_is_refused_on_submit(self):
        """The dropdown can be stale, and the form can be posted directly."""
        self._fill_cart().carrier_id = self.carrier
        form_data = {
            "address_type": "delivery",
            "name": "Test Customer",
            "email": "test.customer@example.com",
            "street": "Test Street 1",
            "city_id": self.unserved_city.id,
            "city": self.unserved_city.name,
            "zip": "10001",
            "state_id": self.state.id,
            "country_id": self.country.id,
        }
        form_data["csrf_token"] = self._csrf_token("/shop/address?address_type=delivery")
        with self._catalog(self.served_city):
            response = self.url_open("/shop/address/submit", data=form_data)
        response.raise_for_status()
        feedback = response.json()
        self.assertIn("city_id", feedback.get("invalid_fields", []))
        self.assertTrue(
            any("not served" in message for message in feedback.get("messages", [])),
            feedback,
        )
