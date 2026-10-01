# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

# In 20.0 the city dropdown of the address form is standard in `portal`
# (`div_city_id`, `cities_data`, `/my/address/state_info`), but only for a few
# countries (`res.country._enforce_city_choice`). This module opens it to every
# country with `enforce_cities` (see models/res_country.py) and keeps on top of it
# what is not standard: the carrier locality catalog at checkout.


from odoo.http import request, route
from odoo.tools import str2bool

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalCity(CustomerPortal):
    def _get_carrier_city_domain(self, state, address_type="billing", use_delivery_as_billing=False, order_sudo=None):
        """Restrict the offered localities to the catalog of the chosen carrier.

        Only the delivery address is concerned: where the parcel is billed is
        no business of the courier. The restriction is skipped when no carrier
        is selected yet, when the carrier has no locality catalog of its own,
        or when its catalog holds no locality in that state - catalog not
        imported yet, or state not covered by the carrier - otherwise the
        customer would be left with an empty list.
        """
        if not state or (address_type != "delivery" and not use_delivery_as_billing):
            return []
        if order_sudo is None:
            # Set by website_sale on every website request; absent on a plain
            # portal one, and gone as soon as the session has no cart.
            order_sudo = getattr(request, "cart", None)
        carrier = order_sudo.carrier_id if order_sudo else None
        if not carrier or not hasattr(carrier, "_get_city_domain"):
            return []
        domain = carrier.sudo()._get_city_domain()
        if not domain:
            return []
        known_cities = request.env["res.city"].sudo().search_count([("state_id", "=", state.id)] + domain, limit=1)
        return domain if known_cities else []

    def _filter_carrier_cities_data(
        self, cities_data, state, address_type="billing", use_delivery_as_billing=False, order_sudo=None
    ):
        """Keep, from the standard `cities_data` (list of dicts), only the carrier's localities."""
        if not cities_data:
            return cities_data
        city_domain = self._get_carrier_city_domain(
            state,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            order_sudo=order_sudo,
        )
        if not city_domain:
            return cities_data
        allowed_ids = set(
            request.env["res.city"].sudo().search([("id", "in", [c["id"] for c in cities_data])] + city_domain).ids
        )
        return [c for c in cities_data if c["id"] in allowed_ids]

    def _prepare_address_form_values(self, partner_sudo, *args, **kwargs):
        rendering_values = super()._prepare_address_form_values(partner_sudo, *args, **kwargs)

        country = rendering_values.get("country") or request.env["res.country"]
        state = rendering_values.get("state") or request.env["res.country.state"]
        cities_data = rendering_values.get("cities_data") or []
        if country._enforce_city_choice():
            if state:
                cities_data = self._filter_carrier_cities_data(
                    cities_data,
                    state,
                    address_type=rendering_values.get("address_type", "billing"),
                    use_delivery_as_billing=rendering_values.get("use_delivery_as_billing", False),
                    order_sudo=kwargs.get("order_sudo") or None,
                )
            elif country.state_ids:
                # The localities come with the state (as in 19.0): do not render the
                # whole catalog of the country (thousands of localities for RO).
                cities_data = []
            rendering_values["cities_data"] = cities_data

        rendering_values["state_cities"] = request.env["res.city"].sudo().browse([c["id"] for c in cities_data])
        return rendering_values

    def _parse_form_data(self, form_data):
        """Fill the free-text city from the chosen locality.

        With enforced cities the form only offers ``city_id`` and the address
        script empties the ``city`` input, while everything downstream (the
        invoice post check, carrier labels, reports) reads ``city``.
        """
        address_values, extra_form_data = super()._parse_form_data(form_data)
        city_id = address_values.get("city_id")
        if city_id and not address_values.get("city"):
            address_values["city"] = request.env["res.city"].sudo().browse(city_id).name
        return address_values, extra_form_data

    def _validate_address_values(self, address_values, partner_sudo, address_type, *args, **kwargs):
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values, partner_sudo, address_type, *args, **kwargs
        )
        city_id = address_values.get("city_id")
        if city_id:
            city = request.env["res.city"].sudo().browse(int(city_id))
            city_domain = self._get_carrier_city_domain(
                city.state_id,
                address_type=address_type,
                use_delivery_as_billing=args[0] if args else kwargs.get("use_delivery_as_billing", False),
            )
            if city_domain and not city.filtered_domain(city_domain):
                invalid_fields.add("city_id")
                error_messages.append(request.env._("The selected city is not served by the chosen delivery method."))
        return invalid_fields, missing_fields, error_messages

    @route()
    def portal_address_state_info(
        self, country_id, state_id=False, address_type="billing", use_delivery_as_billing=False, **kw
    ):
        """Standard route of the address form, restricted to the carrier's localities."""
        result = super().portal_address_state_info(country_id, state_id=state_id, **kw)
        if result.get("cities") and state_id:
            result["cities"] = self._filter_carrier_cities_data(
                result["cities"],
                request.env["res.country.state"].sudo().browse(int(state_id)),
                address_type=address_type,
                use_delivery_as_billing=str2bool(use_delivery_as_billing or "false", default=False),
            )
        return result

    @route(
        '/portal/state_infos/<model("res.country.state"):state>',
        type="jsonrpc",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def state_infos(self, state, address_type="billing", use_delivery_as_billing=False, **kw):
        """Kept for compatibility (used by the 19.0 form); the 20.0 form uses `/my/address/state_info`."""
        city_domain = self._get_carrier_city_domain(
            state,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing in (True, "True", "true", "1"),
        )
        cities = request.env["res.city"].sudo().search([("state_id", "=", state.id)] + city_domain)
        # Return similar tuple structure as website_sale: (id, display_name, zipcode or "")
        return {"cities": [(c.id, c.display_name, c.zipcode or "") for c in cities]}
